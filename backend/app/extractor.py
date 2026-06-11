import asyncio
import logging

import httpx
import trafilatura

from .fetcher import USER_AGENT
from .sanitize import sanitize_html

log = logging.getLogger("newshub.extractor")

EXTRACT_TIMEOUT = 20
MIN_CONTENT_LEN = 200  # below this we consider extraction failed


def _extract_sync(html: str, url: str) -> str:
    result = trafilatura.extract(
        html,
        url=url,
        output_format="html",
        include_images=True,
        include_links=True,
        include_formatting=True,
        favor_precision=True,
    )
    return result or ""


async def extract_content(url: str) -> str:
    try:
        async with httpx.AsyncClient(
            timeout=EXTRACT_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "ru, en;q=0.8"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        extracted = await asyncio.to_thread(_extract_sync, resp.text, url)
        clean = sanitize_html(extracted)
        if len(clean) < MIN_CONTENT_LEN:
            return ""
        return clean
    except Exception as exc:  # noqa: BLE001
        log.warning("extraction failed for %s: %s: %s", url, type(exc).__name__, exc)
        return ""
