from __future__ import annotations

from typing import Protocol


class TelegramNotifier(Protocol):
    async def send_message(self, text: str) -> None:
        ...
