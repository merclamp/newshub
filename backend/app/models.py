from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Kind = Literal["article", "video"]


class Article(BaseModel):
    id: str
    source_id: str
    source_name: str
    kind: Kind = "article"
    title: str
    url: str
    summary: str = ""
    # Full sanitized HTML of the article body (from RSS or on-demand extraction).
    content: str = ""
    image: str = ""
    published: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def published_ts(self) -> float:
        return self.published.timestamp()

    def to_redis(self) -> dict[str, str]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "kind": self.kind,
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "content": self.content,
            "image": self.image,
            "published": self.published.isoformat(),
        }

    @classmethod
    def from_redis(cls, data: dict[str, str]) -> "Article":
        return cls(**data)


class SourceStatus(BaseModel):
    id: str
    name: str
    kind: Kind
    homepage: str = ""
    enabled: bool = True
    last_fetch: datetime | None = None
    last_status: str = "never"  # never | ok | error:<msg>
    article_count: int = 0
