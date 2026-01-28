from __future__ import annotations

import asyncio
import inspect
import logging
import os
from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for path in (PROJECT_ROOT, PROJECT_ROOT / "backend"):
    if path.exists():
        sys.path.insert(0, str(path))

from app.core.logging import setup_logging
from bot.handlers import build_router
from bot.services import BotService

logger = logging.getLogger(__name__)


def _load_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    return token


def _is_dry_run() -> bool:
    return os.getenv("BOT_DRY_RUN", "0") == "1"


async def main() -> None:
    setup_logging()
    dispatcher = Dispatcher()
    service = BotService()
    dispatcher.include_router(build_router(service))
    if _is_dry_run():
        logger.info("BOT_DRY_RUN enabled; bot startup completed without polling.")
        return
    token = _load_bot_token()
    bot_defaults = DefaultBotProperties(parse_mode=ParseMode.HTML)
    if "default" in inspect.signature(Bot.__init__).parameters:
        bot = Bot(token=token, default=bot_defaults)
    else:
        bot = Bot(token=token, parse_mode=ParseMode.HTML)
    logger.info("Starting Telegram bot polling")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
