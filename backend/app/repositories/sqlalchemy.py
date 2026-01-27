from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Referral, User
from app.repositories.interfaces import ReferralRecord, UserRecord


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> UserRecord | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        return UserRecord(id=user.id, telegram_id=user.telegram_id, created_at=user.created_at)

    async def upsert(self, telegram_id: int) -> UserRecord:
        existing = await self.get_by_telegram_id(telegram_id)
        if existing:
            return existing
        user = User(telegram_id=telegram_id)
        self._session.add(user)
        await self._session.flush()
        return UserRecord(id=user.id, telegram_id=user.telegram_id, created_at=user.created_at)


class SqlAlchemyReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_referred(self, referred_telegram_id: int) -> ReferralRecord | None:
        result = await self._session.execute(
            select(Referral).where(Referral.referred_telegram_id == referred_telegram_id)
        )
        referral = result.scalar_one_or_none()
        if not referral:
            return None
        return ReferralRecord(
            id=referral.id,
            referrer_telegram_id=referral.referrer_telegram_id,
            referred_telegram_id=referral.referred_telegram_id,
            created_at=referral.created_at,
        )

    async def create(
        self, referrer_telegram_id: int, referred_telegram_id: int
    ) -> ReferralRecord:
        referral = Referral(
            referrer_telegram_id=referrer_telegram_id,
            referred_telegram_id=referred_telegram_id,
        )
        self._session.add(referral)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise
        return ReferralRecord(
            id=referral.id,
            referrer_telegram_id=referral.referrer_telegram_id,
            referred_telegram_id=referral.referred_telegram_id,
            created_at=referral.created_at,
        )

    async def count_by_referrer(self, referrer_telegram_id: int) -> int:
        result = await self._session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_telegram_id == referrer_telegram_id
            )
        )
        return int(result.scalar_one())

    async def last_referrals(
        self, referrer_telegram_id: int, limit: int = 5
    ) -> list[ReferralRecord]:
        result = await self._session.execute(
            select(Referral)
            .where(Referral.referrer_telegram_id == referrer_telegram_id)
            .order_by(Referral.created_at.desc())
            .limit(limit)
        )
        referrals = result.scalars().all()
        return [
            ReferralRecord(
                id=referral.id,
                referrer_telegram_id=referral.referrer_telegram_id,
                referred_telegram_id=referral.referred_telegram_id,
                created_at=referral.created_at,
            )
            for referral in referrals
        ]
