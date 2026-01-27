from __future__ import annotations

from app.repositories.interfaces import ReferralRepository, UserRepository
from app.usecases.errors import NotFoundError, ValidationError


class UpsertUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, telegram_id: int):
        if telegram_id <= 0:
            raise ValidationError("telegram_id must be positive")
        return await self._users.upsert(telegram_id)


class GetUserStatus:
    def __init__(self, users: UserRepository, referrals: ReferralRepository) -> None:
        self._users = users
        self._referrals = referrals

    async def execute(self, telegram_id: int):
        if telegram_id <= 0:
            raise ValidationError("telegram_id must be positive")
        user = await self._users.get_by_telegram_id(telegram_id)
        if not user:
            raise NotFoundError("user not found")
        referred = await self._referrals.get_by_referred(telegram_id)
        referral_count = await self._referrals.count_by_referrer(telegram_id)
        return {
            "telegram_id": telegram_id,
            "referred_by": referred.referrer_telegram_id if referred else None,
            "referral_count": referral_count,
        }
