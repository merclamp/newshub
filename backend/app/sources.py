from dataclasses import dataclass, field

from .models import Kind

YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: Kind
    url: str
    homepage: str = ""
    enabled: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)
    stream_timeout: float = 0


def yt(source_id: str, name: str, channel_id: str, homepage: str = "", enabled: bool = True) -> Source:
    return Source(
        id=source_id,
        name=name,
        kind="video",
        url=YOUTUBE_FEED.format(cid=channel_id),
        homepage=homepage or f"https://www.youtube.com/channel/{channel_id}",
        enabled=enabled,
    )


SOURCES: list[Source] = [
    Source(
        id="dw",
        name="DW Россия",
        kind="article",
        url="https://rss.dw.com/xml/rss-ru-all",
        homepage="https://www.dw.com/ru/",
    ),
    Source(
        id="meduza",
        name="Meduza",
        kind="article",
        url="https://meduza.io/rss/all",
        homepage="https://meduza.io",
    ),
    Source(
        id="tvrain",
        name="Дождь",
        kind="article",
        url="https://tvrain.tv/export/rss/all.xml",
        homepage="https://tvrain.tv",
    ),
    Source(
        id="khodorkovsky",
        name="Ходорковский",
        kind="article",
        url="https://khodorkovsky.com/feed/",
        homepage="https://khodorkovsky.com",
    ),
    Source(
        id="rabkor",
        name="Рабкор",
        kind="article",
        url="https://rabkor.ru/feed/",
        homepage="https://rabkor.ru",
        stream_timeout=15,
    ),
    Source(
        id="newsmaker",
        name="NewsMaker",
        kind="article",
        url="https://newsmaker.md/feed",
        homepage="https://newsmaker.md",
    ),

    yt("dw-yt", "DW на русском (YouTube)", "UCXoAjrdHFa2hEL3Ug8REC1w"),
    yt("meduza-yt", "MeduzaLive (YouTube)", "UCKQeWVS92LRgnyM432POuwQ"),
    yt("tvrain-yt", "Дождь (YouTube)", "UCdubelOloxR3wzwJG9x8YqQ"),
    yt("khodorkovsky-yt", "Ходорковский LIVE (YouTube)", "UCBzDAjLfvBUBVMMP6-K-y0w"),
    yt("rabkor-yt", "Рабкор (YouTube)", "UCYDuWqDwzAFG4xrI5uJEWfw"),
    yt("newsmaker-yt", "NewsMaker (YouTube)", "UCRk7uMJLm68va162_gEmJLA"),
    yt("nexta-yt", "NEXTA Live (YouTube)", "UCrp2It0yWUC7XcrWyBIQeKw"),
]

SOURCES_BY_ID: dict[str, Source] = {s.id: s for s in SOURCES}


def enabled_sources() -> list[Source]:
    return [s for s in SOURCES if s.enabled]
