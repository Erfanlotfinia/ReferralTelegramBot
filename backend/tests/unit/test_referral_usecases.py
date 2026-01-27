from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.interfaces import ReferralRecord
from app.usecases.errors import ConflictError, ValidationError
from app.usecases.referrals import CreateReferral


@dataclass
class FakeReferralRepository:
    referrals: dict[int, ReferralRecord]
    next_id: int = 1

    async def get_by_referred(self, referred_telegram_id: int) -> ReferralRecord | None:
        return self.referrals.get(referred_telegram_id)

    async def create(
        self, referrer_telegram_id: int, referred_telegram_id: int
    ) -> ReferralRecord:
        if referred_telegram_id in self.referrals:
            raise IntegrityError("insert", {}, Exception("duplicate"))
        record = ReferralRecord(
            id=self.next_id,
            referrer_telegram_id=referrer_telegram_id,
            referred_telegram_id=referred_telegram_id,
            created_at=datetime.now(timezone.utc),
        )
        self.referrals[referred_telegram_id] = record
        self.next_id += 1
        return record

    async def count_by_referrer(self, referrer_telegram_id: int) -> int:
        return sum(
            1
            for referral in self.referrals.values()
            if referral.referrer_telegram_id == referrer_telegram_id
        )

    async def last_referrals(self, referrer_telegram_id: int, limit: int = 5):
        return [
            referral
            for referral in self.referrals.values()
            if referral.referrer_telegram_id == referrer_telegram_id
        ][:limit]


class IntegrityOnceReferralRepository(FakeReferralRepository):
    def __init__(self, referrals: dict[int, ReferralRecord]) -> None:
        super().__init__(referrals=referrals)
        self._raised = False

    async def create(
        self, referrer_telegram_id: int, referred_telegram_id: int
    ) -> ReferralRecord:
        if not self._raised:
            self._raised = True
            raise IntegrityError("insert", {}, Exception("duplicate"))
        return await super().create(referrer_telegram_id, referred_telegram_id)


@pytest.mark.asyncio
async def test_create_referral_idempotent_same_referrer() -> None:
    repo = FakeReferralRepository(referrals={})
    usecase = CreateReferral(repo)
    created, was_created = await usecase.execute(10, 20)
    assert was_created is True
    existing, was_created = await usecase.execute(10, 20)
    assert existing == created
    assert was_created is False


@pytest.mark.asyncio
async def test_create_referral_conflict_different_referrer() -> None:
    repo = FakeReferralRepository(referrals={})
    usecase = CreateReferral(repo)
    await usecase.execute(10, 20)
    with pytest.raises(ConflictError):
        await usecase.execute(11, 20)


@pytest.mark.asyncio
async def test_create_referral_self_referral_rejected() -> None:
    repo = FakeReferralRepository(referrals={})
    usecase = CreateReferral(repo)
    with pytest.raises(ValidationError):
        await usecase.execute(10, 10)


@pytest.mark.asyncio
async def test_create_referral_integrity_error_returns_existing() -> None:
    existing = ReferralRecord(
        id=1,
        referrer_telegram_id=10,
        referred_telegram_id=20,
        created_at=datetime.now(timezone.utc),
    )
    repo = IntegrityOnceReferralRepository(referrals={20: existing})
    usecase = CreateReferral(repo)
    referral, created = await usecase.execute(10, 20)
    assert referral == existing
    assert created is False
