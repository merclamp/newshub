from dataclasses import dataclass, field

from .models import Kind


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
]

SOURCES_BY_ID: dict[str, Source] = {s.id: s for s in SOURCES}


def enabled_sources() -> list[Source]:
    return [s for s in SOURCES if s.enabled]
