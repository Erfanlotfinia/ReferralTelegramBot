from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class UserRecord:
    id: int
    telegram_id: int
    created_at: datetime


@dataclass(frozen=True)
class ReferralRecord:
    id: int
    referrer_telegram_id: int
    referred_telegram_id: int
    created_at: datetime


class UserRepository(Protocol):
    async def get_by_telegram_id(self, telegram_id: int) -> UserRecord | None:
        ...

    async def upsert(self, telegram_id: int) -> UserRecord:
        ...


class ReferralRepository(Protocol):
    async def get_by_referred(self, referred_telegram_id: int) -> ReferralRecord | None:
        ...

    async def create(
        self, referrer_telegram_id: int, referred_telegram_id: int
    ) -> ReferralRecord:
        ...

    async def count_by_referrer(self, referrer_telegram_id: int) -> int:
        ...

    async def last_referrals(
        self, referrer_telegram_id: int, limit: int = 5
    ) -> list[ReferralRecord]:
        ...
