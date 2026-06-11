"""Telegram digest bot (aiogram 3).

Run with:  python -m app.bot.main

Commands:
    /start        — welcome + help
    /subscribe    — subscribe to the periodic digest
    /unsubscribe  — unsubscribe
    /digest       — get a digest right now (items since your last digest)
    /sources      — list of sources and their status
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import LinkPreviewOptions, Message

from .. import storage
from ..config import get_settings
from ..redis_client import close_redis, get_redis
from .digest import build_digest_messages

log = logging.getLogger("newshub.bot")
router = Router()

HELP_TEXT = (
    "<b>🗞 NewsHub</b> — агрегатор новостей независимых СМИ.\n\n"
    "Я присылаю периодические дайджесты новых статей и видео.\n\n"
    "<b>Команды:</b>\n"
    "/subscribe — подписаться на дайджест\n"
    "/unsubscribe — отписаться\n"
    "/digest — получить дайджест прямо сейчас\n"
    "/sources — список источников"
)


async def send_digest_to(bot: Bot, chat_id: int, since_ts: float) -> bool:
    """Build and send a digest of items newer than since_ts. Returns True if sent."""
    r = get_redis()
    articles = await storage.get_articles_since(r, since_ts)
    since_dt = datetime.fromtimestamp(since_ts, tz=timezone.utc)
    messages = build_digest_messages(articles, since=since_dt)
    if not messages:
        return False
    for msg in messages:
        await bot.send_message(
            chat_id,
            msg,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    await storage.set_last_digest_ts(r, chat_id, time.time())
    return True


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    r = get_redis()
    settings = get_settings()
    added = await storage.add_subscriber(r, message.chat.id)
    if added:
        await storage.set_last_digest_ts(r, message.chat.id, time.time())
        await message.answer(
            f"✅ Подписка оформлена. Дайджест будет приходить каждые "
            f"{settings.digest_interval_hours} ч. (если есть новые материалы)."
        )
    else:
        await message.answer("Вы уже подписаны. /digest — получить сводку сейчас.")


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message) -> None:
    r = get_redis()
    removed = await storage.remove_subscriber(r, message.chat.id)
    await message.answer("☑️ Подписка отменена." if removed else "Вы и не были подписаны.")


@router.message(Command("digest"))
async def cmd_digest(message: Message, bot: Bot) -> None:
    settings = get_settings()
    r = get_redis()
    last_ts = await storage.get_last_digest_ts(r, message.chat.id)
    if last_ts is None:
        last_ts = (
            datetime.now(timezone.utc)
            - timedelta(hours=settings.digest_lookback_hours_default)
        ).timestamp()
    sent = await send_digest_to(bot, message.chat.id, last_ts)
    if not sent:
        await message.answer("Пока нет новых материалов. Попробуйте позже.")


@router.message(Command("sources"))
async def cmd_sources(message: Message) -> None:
    r = get_redis()
    statuses = await storage.get_sources_status(r)
    lines = ["<b>Источники:</b>"]
    for s in statuses:
        mark = "🟢" if s.last_status == "ok" else ("⚪️" if s.last_status == "never" else "🔴")
        icon = "🎬" if s.kind == "video" else "📰"
        lines.append(f"{mark} {icon} {s.name} — {s.article_count} материалов")
    await message.answer("\n".join(lines))


async def digest_loop(bot: Bot) -> None:
    """Periodically send digests to all subscribers."""
    settings = get_settings()
    interval = settings.digest_interval_hours * 3600
    r = get_redis()
    while True:
        await asyncio.sleep(interval)
        subscribers = await storage.get_subscribers(r)
        log.info("digest tick: %d subscribers", len(subscribers))
        for chat_id in subscribers:
            last_ts = await storage.get_last_digest_ts(r, chat_id)
            if last_ts is None:
                last_ts = time.time() - interval
            try:
                await send_digest_to(bot, chat_id, last_ts)
            except TelegramForbiddenError:
                log.info("chat %s blocked the bot, unsubscribing", chat_id)
                await storage.remove_subscriber(r, chat_id)
            except Exception:  # noqa: BLE001
                log.exception("failed to send digest to %s", chat_id)
            await asyncio.sleep(0.2)  # be gentle with Telegram rate limits


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    if not settings.bot_token:
        log.error("BOT_TOKEN is not set — digest bot cannot start.")
        sys.exit(1)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    loop_task = asyncio.create_task(digest_loop(bot))
    log.info("digest bot started, interval %dh", settings.digest_interval_hours)
    try:
        await dp.start_polling(bot)
    finally:
        loop_task.cancel()
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
