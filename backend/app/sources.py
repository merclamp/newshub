import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .config import get_settings
from .models import Kind

log = logging.getLogger(__name__)


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


def _load_sources() -> list[Source]:
    settings = get_settings()
    path = Path(settings.sources_file)
    if not path.exists():
        log.warning("sources file not found: %s — no sources loaded", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.error("failed to load sources from %s: %s", path, exc)
        return []
    sources: list[Source] = []
    for item in data:
        try:
            sources.append(Source(**item))
        except TypeError as exc:
            log.warning("skipping invalid source entry in %s: %s", path, exc)
    return sources


SOURCES: list[Source] = _load_sources()
SOURCES_BY_ID: dict[str, Source] = {s.id: s for s in SOURCES}


def enabled_sources() -> list[Source]:
    return [s for s in SOURCES if s.enabled]
