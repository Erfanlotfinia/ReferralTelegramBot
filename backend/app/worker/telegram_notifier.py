from __future__ import annotations

import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


class AiogramTelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self._bot = Bot(token=token)
        self._chat_id = chat_id

    async def send_message(self, text: str) -> None:
        await self._bot.send_message(chat_id=self._chat_id, text=text)


class NullTelegramNotifier:
    async def send_message(self, text: str) -> None:
        logger.info("Telegram notifier disabled; message=%s", text)
