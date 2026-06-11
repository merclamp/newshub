import asyncio
import logging

from . import storage
from .config import get_settings
from .fetcher import fetch_all
from .redis_client import close_redis, get_redis
from .sources import enabled_sources

log = logging.getLogger("newshub.worker")


async def run_cycle() -> None:
    r = get_redis()
    sources = enabled_sources()
    results = await fetch_all(sources)

    total_new = 0
    for source in sources:
        result = results.get(source.id)
        if isinstance(result, Exception):
            msg = f"{type(result).__name__}: {result}"
            log.warning("source %s failed: %s", source.id, msg)
            await storage.set_source_status(r, source.id, f"error:{msg[:200]}")
            continue
        new = await storage.save_articles(r, result or [])
        total_new += new
        await storage.set_source_status(r, source.id, "ok")
        if new:
            log.info("source %s: +%d new items", source.id, new)

    await storage.trim_old(r)
    log.info("cycle done: %d new items total", total_new)


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log.info(
        "worker started: %d sources, interval %ds",
        len(enabled_sources()),
        settings.fetch_interval_seconds,
    )
    try:
        while True:
            try:
                await run_cycle()
            except Exception:  # noqa: BLE001 — keep the loop alive
                log.exception("fetch cycle crashed")
            await asyncio.sleep(settings.fetch_interval_seconds)
    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
