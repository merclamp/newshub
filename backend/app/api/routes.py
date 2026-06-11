from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from .. import storage
from ..extractor import extract_content
from ..models import Article, SourceStatus
from ..redis_client import get_redis
from ..sources import SOURCES_BY_ID

router = APIRouter(prefix="/api")

@router.get("/health")
async def health() -> dict:
    r = get_redis()
    try:
        await r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok" if redis_ok else "degraded", "redis": redis_ok}


@router.get("/news", response_model=list[Article])
async def news(
    source: str | None = Query(default=None, description="Source id, e.g. 'meduza'"),
    kind: Literal["article", "video"] | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Article]:
    if source is not None and source not in SOURCES_BY_ID:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")
    r = get_redis()
    return await storage.get_feed(r, source_id=source, kind=kind, limit=limit, offset=offset)


@router.get("/news/{article_id}", response_model=Article)
async def news_item(article_id: str) -> Article:
    """Article details. For articles without full text in the feed,
    extracts it from the original page on first request and caches it."""
    r = get_redis()
    data = await r.hgetall(storage.k_article(article_id))
    if not data:
        raise HTTPException(status_code=404, detail="Article not found or expired")
    article = Article.from_redis(data)
    if article.kind == "article" and not article.content:
        content = await extract_content(article.url)
        if content:
            article.content = content
            await r.hset(storage.k_article(article_id), "content", content)
    return article


@router.get("/sources", response_model=list[SourceStatus])
async def sources() -> list[SourceStatus]:
    r = get_redis()
    return await storage.get_sources_status(r)


@router.get("/stats")
async def stats() -> dict:
    r = get_redis()
    return {
        "total": await storage.count_feed(r),
        "articles": await storage.count_feed(r, kind="article"),
        "videos": await storage.count_feed(r, kind="video"),
        "sources": len(SOURCES_BY_ID),
    }
