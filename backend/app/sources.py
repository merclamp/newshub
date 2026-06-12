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


from .sources_data import SOURCES  # noqa: E402

SOURCES_BY_ID: dict[str, Source] = {s.id: s for s in SOURCES}


def enabled_sources() -> list[Source]:
    return [s for s in SOURCES if s.enabled]
