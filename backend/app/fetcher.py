import asyncio
import hashlib
import html
import logging
import re
from datetime import datetime, timezone
import feedparser
import httpx

from .config import get_settings
from .models import Article
from .sanitize import sanitize_html
from .sources import Source

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 NewsHub/1.0"
)

TAG_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
WS_RE = re.compile(r"\s+")

SUMMARY_MAX_LEN = 500


def make_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def strip_html(text: str) -> str:
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return WS_RE.sub(" ", text).strip()


def _entry_published(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
    return datetime.now(timezone.utc)


def _entry_image(entry, raw_summary: str) -> str:
    # YouTube / Media RSS thumbnails
    thumbs = getattr(entry, "media_thumbnail", None) or []
    for t in thumbs:
        if t.get("url"):
            return t["url"]
    media = getattr(entry, "media_content", None) or []
    for m in media:
        if m.get("medium") == "image" and m.get("url"):
            return m["url"]
    for enc in getattr(entry, "enclosures", None) or []:
        if str(enc.get("type", "")).startswith("image") and enc.get("href"):
            return enc["href"]
    match = IMG_RE.search(raw_summary)
    return match.group(1) if match else ""


def _entry_content(entry) -> str:
    """Full article body from RSS, if the feed provides it (content:encoded)."""
    for c in getattr(entry, "content", None) or []:
        value = c.get("value") if isinstance(c, dict) else getattr(c, "value", "")
        if value and len(value) > 300:
            return value
    return ""


def _entry_summary(entry) -> str:
    raw = ""
    if getattr(entry, "summary", None):
        raw = entry.summary
    elif getattr(entry, "description", None):
        raw = entry.description
    # YouTube puts the description in media:group
    elif getattr(entry, "media_description", None):
        raw = entry.media_description
    return raw


def parse_feed(source: Source, content: bytes) -> list[Article]:
    parsed = feedparser.parse(content)
    articles: list[Article] = []
    for entry in parsed.entries:
        url = getattr(entry, "link", "") or ""
        title = strip_html(getattr(entry, "title", "") or "")
        if not url or not title:
            continue
        raw_summary = _entry_summary(entry)
        summary = strip_html(raw_summary)
        if len(summary) > SUMMARY_MAX_LEN:
            summary = summary[: SUMMARY_MAX_LEN - 1].rsplit(" ", 1)[0] + "…"
        content = ""
        if source.kind == "article":
            content = sanitize_html(_entry_content(entry))
        articles.append(
            Article(
                id=make_id(url),
                source_id=source.id,
                source_name=source.name,
                kind=source.kind,
                title=title,
                url=url,
                summary=summary,
                content=content,
                image=_entry_image(entry, raw_summary),
                published=_entry_published(entry),
            )
        )
    return articles


def _trim_to_valid_utf8(data: bytes) -> bytes:
    for cutoff in range(len(data), max(0, len(data) - 4), -1):
        try:
            data[:cutoff].decode("utf-8")
            return data[:cutoff]
        except UnicodeDecodeError:
            continue
    return data


async def _stream_fetch(client: httpx.AsyncClient, source: Source) -> list[Article]:
    """Stream a feed that may hang mid-response. Returns whatever we got."""
    chunks: list[bytes] = []
    try:
        async with client.stream("GET", source.url) as resp:
            resp.raise_for_status()
            async with asyncio.timeout(source.stream_timeout):
                async for chunk in resp.aiter_bytes():
                    chunks.append(chunk)
    except (asyncio.TimeoutError, httpx.ReadTimeout):
        pass
    raw = _trim_to_valid_utf8(b"".join(chunks))
    if not raw:
        raise RuntimeError("stream_read_timeout: no data received")
    return await asyncio.to_thread(parse_feed, source, raw)


async def fetch_source(client: httpx.AsyncClient, source: Source) -> list[Article]:
    """Download and parse a single feed. Raises on HTTP errors."""
    if source.stream_timeout > 0:
        return await _stream_fetch(client, source)
    resp = await client.get(source.url)
    resp.raise_for_status()
    return await asyncio.to_thread(parse_feed, source, resp.content)


async def fetch_all(sources: list[Source]) -> dict[str, list[Article] | Exception]:
    """Fetch all sources concurrently. Returns per-source results or errors."""
    settings = get_settings()
    semaphore = asyncio.Semaphore(settings.fetch_concurrency)
    results: dict[str, list[Article] | Exception] = {}

    async with httpx.AsyncClient(
        timeout=settings.fetch_timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"},
    ) as client:

        async def one(source: Source) -> None:
            async with semaphore:
                try:
                    results[source.id] = await fetch_source(client, source)
                except Exception as exc:  # noqa: BLE001 — one bad feed must not kill the cycle
                    results[source.id] = exc

        await asyncio.gather(*(one(s) for s in sources))

    return results
