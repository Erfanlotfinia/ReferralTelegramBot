from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserUpsertRequest(BaseModel):
    telegram_id: int


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    created_at: datetime


class ReferralCreateRequest(BaseModel):
    referrer_telegram_id: int
    referred_telegram_id: int


class ReferralResponse(BaseModel):
    id: int
    referrer_telegram_id: int
    referred_telegram_id: int
    created_at: datetime


class UserStatusResponse(BaseModel):
    telegram_id: int
    referred_by: int | None
    referral_count: int


class ReferralSummaryItem(BaseModel):
    referred_telegram_id: int
    created_at: datetime


class ReferralSummaryResponse(BaseModel):
    referrer_telegram_id: int
    count: int
    last_5_referrals: list[ReferralSummaryItem]
