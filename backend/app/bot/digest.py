"""Digest building: group articles by source and format Telegram HTML messages."""

import html
from collections import defaultdict
from datetime import datetime, timezone

from ..config import get_settings
from ..models import Article

TG_MESSAGE_LIMIT = 4096

KIND_ICON = {"article": "📰", "video": "🎬"}


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def group_by_source(articles: list[Article], max_per_source: int) -> dict[str, list[Article]]:
    grouped: dict[str, list[Article]] = defaultdict(list)
    for art in sorted(articles, key=lambda a: a.published_ts, reverse=True):
        if len(grouped[art.source_name]) < max_per_source:
            grouped[art.source_name].append(art)
    return dict(grouped)


def build_digest_messages(articles: list[Article], since: datetime | None = None) -> list[str]:
    """Returns a list of HTML messages, each within the Telegram length limit."""
    settings = get_settings()
    if not articles:
        return []

    grouped = group_by_source(articles, settings.digest_max_per_source)

    now = datetime.now(timezone.utc)
    header = f"<b>🗞 NewsHub — дайджест</b>\n<i>{now.strftime('%d.%m.%Y %H:%M')} UTC</i>"
    if since is not None:
        header += f"\n<i>новые материалы с {since.strftime('%d.%m %H:%M')} UTC</i>"

    blocks: list[str] = []
    for source_name, items in grouped.items():
        lines = [f"\n<b>{esc(source_name)}</b>"]
        for art in items:
            icon = KIND_ICON.get(art.kind, "•")
            lines.append(f'{icon} <a href="{art.url}">{esc(art.title)}</a>')
        blocks.append("\n".join(lines))

    messages: list[str] = []
    current = header
    for block in blocks:
        candidate = current + "\n" + block
        if len(candidate) > TG_MESSAGE_LIMIT:
            messages.append(current)
            current = block.lstrip("\n")
        else:
            current = candidate
    if current.strip():
        messages.append(current)
    return messages
