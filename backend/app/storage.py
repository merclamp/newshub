import time
from datetime import datetime, timezone

import redis.asyncio as redis

from .config import get_settings
from .models import Article, SourceStatus
from .sources import SOURCES

PREFIX = "nh"


def k_article(article_id: str) -> str:
    return f"{PREFIX}:article:{article_id}"


def k_seen(article_id: str) -> str:
    return f"{PREFIX}:seen:{article_id}"


K_FEED_ALL = f"{PREFIX}:feed:all"


def k_feed_src(source_id: str) -> str:
    return f"{PREFIX}:feed:src:{source_id}"


def k_feed_kind(kind: str) -> str:
    return f"{PREFIX}:feed:kind:{kind}"


K_SUBSCRIBERS = f"{PREFIX}:digest:subscribers"

async def save_articles(r: redis.Redis, articles: list[Article]) -> int:
    """Store articles that were not seen before. Returns number of new ones."""
    settings = get_settings()
    new_count = 0
    for art in articles:
        # SET NX serves as an atomic dedup gate.
        is_new = await r.set(k_seen(art.id), "1", ex=settings.seen_ttl_seconds, nx=True)
        if not is_new:
            continue
        ts = art.published_ts
        pipe = r.pipeline(transaction=False)
        pipe.hset(k_article(art.id), mapping=art.to_redis())
        pipe.expire(k_article(art.id), settings.article_ttl_seconds)
        pipe.zadd(K_FEED_ALL, {art.id: ts})
        pipe.zadd(k_feed_src(art.source_id), {art.id: ts})
        pipe.zadd(k_feed_kind(art.kind), {art.id: ts})
        await pipe.execute()
        new_count += 1
    return new_count


async def _fetch_articles(r: redis.Redis, ids: list[str]) -> list[Article]:
    if not ids:
        return []
    pipe = r.pipeline(transaction=False)
    for aid in ids:
        pipe.hgetall(k_article(aid))
    rows = await pipe.execute()
    return [Article.from_redis(row) for row in rows if row]


async def get_feed(
    r: redis.Redis,
    source_id: str | None = None,
    kind: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[Article]:
    if source_id:
        key = k_feed_src(source_id)
    elif kind:
        key = k_feed_kind(kind)
    else:
        key = K_FEED_ALL

    if source_id and kind:
        # Rare combination: filter in Python after fetching a wider window.
        ids = await r.zrevrange(k_feed_src(source_id), 0, offset + limit * 4)
        articles = [a for a in await _fetch_articles(r, ids) if a.kind == kind]
        return articles[offset : offset + limit]

    ids = await r.zrevrange(key, offset, offset + limit - 1)
    return await _fetch_articles(r, ids)


async def get_articles_since(
    r: redis.Redis, since_ts: float, max_total: int = 200
) -> list[Article]:
    ids = await r.zrevrangebyscore(K_FEED_ALL, "+inf", f"({since_ts}", start=0, num=max_total)
    return await _fetch_articles(r, ids)


async def count_feed(r: redis.Redis, source_id: str | None = None, kind: str | None = None) -> int:
    if source_id:
        return await r.zcard(k_feed_src(source_id))
    if kind:
        return await r.zcard(k_feed_kind(kind))
    return await r.zcard(K_FEED_ALL)


async def trim_old(r: redis.Redis) -> None:
    settings = get_settings()
    horizon = time.time() - settings.article_ttl_seconds
    keys = [K_FEED_ALL, k_feed_kind("article"), k_feed_kind("video")]
    keys += [k_feed_src(s.id) for s in SOURCES]
    pipe = r.pipeline(transaction=False)
    for key in keys:
        pipe.zremrangebyscore(key, "-inf", horizon)
    pipe.zremrangebyrank(K_FEED_ALL, 0, -settings.max_feed_size - 1)
    await pipe.execute()

async def set_source_status(r: redis.Redis, source_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    pipe = r.pipeline(transaction=False)
    pipe.set(f"{PREFIX}:src:{source_id}:last_fetch", now)
    pipe.set(f"{PREFIX}:src:{source_id}:status", status)
    await pipe.execute()


async def get_sources_status(r: redis.Redis) -> list[SourceStatus]:
    pipe = r.pipeline(transaction=False)
    for s in SOURCES:
        pipe.get(f"{PREFIX}:src:{s.id}:last_fetch")
        pipe.get(f"{PREFIX}:src:{s.id}:status")
        pipe.zcard(k_feed_src(s.id))
    rows = await pipe.execute()
    result = []
    for i, s in enumerate(SOURCES):
        last_fetch, status, count = rows[i * 3], rows[i * 3 + 1], rows[i * 3 + 2]
        result.append(
            SourceStatus(
                id=s.id,
                name=s.name,
                kind=s.kind,
                homepage=s.homepage,
                enabled=s.enabled,
                last_fetch=datetime.fromisoformat(last_fetch) if last_fetch else None,
                last_status=status or "never",
                article_count=count,
            )
        )
    return result

async def add_subscriber(r: redis.Redis, chat_id: int) -> bool:
    return bool(await r.sadd(K_SUBSCRIBERS, str(chat_id)))


async def remove_subscriber(r: redis.Redis, chat_id: int) -> bool:
    return bool(await r.srem(K_SUBSCRIBERS, str(chat_id)))


async def get_subscribers(r: redis.Redis) -> list[int]:
    return [int(x) for x in await r.smembers(K_SUBSCRIBERS)]


async def is_subscriber(r: redis.Redis, chat_id: int) -> bool:
    return bool(await r.sismember(K_SUBSCRIBERS, str(chat_id)))


async def get_last_digest_ts(r: redis.Redis, chat_id: int) -> float | None:
    val = await r.get(f"{PREFIX}:digest:last:{chat_id}")
    return float(val) if val else None


async def set_last_digest_ts(r: redis.Redis, chat_id: int, ts: float) -> None:
    await r.set(f"{PREFIX}:digest:last:{chat_id}", repr(ts))
