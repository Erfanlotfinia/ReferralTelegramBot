from __future__ import annotations

import logging
from sqlalchemy.exc import IntegrityError

from app.repositories.interfaces import ReferralRepository
from app.usecases.errors import ConflictError, ValidationError

logger = logging.getLogger(__name__)


class CreateReferral:
    def __init__(self, referrals: ReferralRepository) -> None:
        self._referrals = referrals

    async def execute(self, referrer_telegram_id: int, referred_telegram_id: int):
        if referrer_telegram_id <= 0 or referred_telegram_id <= 0:
            raise ValidationError("telegram ids must be positive")
        if referrer_telegram_id == referred_telegram_id:
            raise ValidationError("referrer and referred cannot be the same")
        existing = await self._referrals.get_by_referred(referred_telegram_id)
        if existing:
            if existing.referrer_telegram_id == referrer_telegram_id:
                return existing, False
            raise ConflictError("referred user already has a referrer")
        try:
            created = await self._referrals.create(referrer_telegram_id, referred_telegram_id)
            return created, True
        except IntegrityError:
            logger.info("Referral integrity conflict; resolving idempotently")
            existing = await self._referrals.get_by_referred(referred_telegram_id)
            if existing and existing.referrer_telegram_id == referrer_telegram_id:
                return existing, False
            raise ConflictError("referred user already has a referrer")


class GetReferralSummary:
    def __init__(self, referrals: ReferralRepository) -> None:
        self._referrals = referrals

    async def execute(self, referrer_telegram_id: int):
        if referrer_telegram_id <= 0:
            raise ValidationError("telegram_id must be positive")
        count = await self._referrals.count_by_referrer(referrer_telegram_id)
        last_referrals = await self._referrals.last_referrals(referrer_telegram_id)
        return {
            "referrer_telegram_id": referrer_telegram_id,
            "count": count,
            "last_5_referrals": [
                {
                    "referred_telegram_id": referral.referred_telegram_id,
                    "created_at": referral.created_at,
                }
                for referral in last_referrals
            ],
        }
