from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.repositories.interfaces import ReferralRecord, UserRecord
from app.usecases.errors import NotFoundError, ValidationError
from app.usecases.users import GetUserStatus, UpsertUser


@dataclass
class FakeUserRepository:
    users: dict[int, UserRecord]
    next_id: int = 1

    async def get_by_telegram_id(self, telegram_id: int) -> UserRecord | None:
        return self.users.get(telegram_id)

    async def upsert(self, telegram_id: int) -> UserRecord:
        existing = self.users.get(telegram_id)
        if existing:
            return existing
        record = UserRecord(
            id=self.next_id,
            telegram_id=telegram_id,
            created_at=datetime.now(timezone.utc),
        )
        self.users[telegram_id] = record
        self.next_id += 1
        return record


@dataclass
class FakeReferralRepository:
    referrals: dict[int, ReferralRecord]

    async def get_by_referred(self, referred_telegram_id: int) -> ReferralRecord | None:
        return self.referrals.get(referred_telegram_id)

    async def create(
        self, referrer_telegram_id: int, referred_telegram_id: int
    ) -> ReferralRecord:
        raise NotImplementedError

    async def count_by_referrer(self, referrer_telegram_id: int) -> int:
        return sum(
            1
            for referral in self.referrals.values()
            if referral.referrer_telegram_id == referrer_telegram_id
        )

    async def last_referrals(self, referrer_telegram_id: int, limit: int = 5):
        return []


@pytest.mark.asyncio
async def test_upsert_user_rejects_invalid_id() -> None:
    repo = FakeUserRepository(users={})
    usecase = UpsertUser(repo)
    with pytest.raises(ValidationError):
        await usecase.execute(0)


@pytest.mark.asyncio
async def test_get_user_status_not_found() -> None:
    users = FakeUserRepository(users={})
    referrals = FakeReferralRepository(referrals={})
    usecase = GetUserStatus(users, referrals)
    with pytest.raises(NotFoundError):
        await usecase.execute(999)


@pytest.mark.asyncio
async def test_get_user_status_returns_summary() -> None:
    user = UserRecord(
        id=1, telegram_id=42, created_at=datetime.now(timezone.utc)
    )
    referral = ReferralRecord(
        id=1,
        referrer_telegram_id=7,
        referred_telegram_id=42,
        created_at=datetime.now(timezone.utc),
    )
    users = FakeUserRepository(users={42: user})
    referrals = FakeReferralRepository(referrals={42: referral})
    usecase = GetUserStatus(users, referrals)
    result = await usecase.execute(42)
    assert result["referred_by"] == 7
    assert result["referral_count"] == 0
