from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Infrastructure
    redis_url: str = "redis://localhost:6379/0"

    # Fetcher
    fetch_interval_seconds: int = 300
    fetch_timeout_seconds: int = 25
    fetch_concurrency: int = 8
    article_ttl_days: int = 7
    # "seen" markers live longer than articles so expired items don't reappear
    seen_ttl_days: int = 30
    max_feed_size: int = 1000

    # API
    cors_origins: str = "*"

    # Telegram digest bot
    bot_token: str = ""
    digest_interval_hours: int = 6
    digest_max_per_source: int = 5
    digest_lookback_hours_default: int = 24

    @property
    def article_ttl_seconds(self) -> int:
        return self.article_ttl_days * 86400

    @property
    def seen_ttl_seconds(self) -> int:
        return self.seen_ttl_days * 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
