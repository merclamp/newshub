from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Infrastructure
    redis_url: str = "redis://localhost:6379/0"

    # Fetcher
    sources_file: str = "sources.json"
    fetch_interval_seconds: int = 3600
    fetch_timeout_seconds: int = 25
    fetch_concurrency: int = 8
    article_ttl_days: int = 7
    # "seen" markers live longer than articles so expired items don't reappear
    seen_ttl_days: int = 30
    max_feed_size: int = 1000

    # API
    cors_origins: str = ""

    @property
    def article_ttl_seconds(self) -> int:
        return self.article_ttl_days * 86400

    @property
    def seen_ttl_seconds(self) -> int:
        return self.seen_ttl_days * 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
