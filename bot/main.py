from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from app.core.logging import setup_logging
from bot.handlers import build_router
from bot.services import BotService

logger = logging.getLogger(__name__)


def _load_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    return token


async def main() -> None:
    setup_logging()
    token = _load_bot_token()
    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    dispatcher = Dispatcher()
    service = BotService()
    dispatcher.include_router(build_router(service))
    logger.info("Starting Telegram bot polling")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
