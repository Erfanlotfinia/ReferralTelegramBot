from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import Response
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import create_referral, get_user_status
from app.db.models import Base
from app.db.session import UnitOfWork
from app.schemas import ReferralCreateRequest


@pytest.mark.asyncio
async def test_create_referral_upserts_users(tmp_path: Path) -> None:
    db_path = tmp_path / "referrals.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    def build_uow() -> UnitOfWork:
        return UnitOfWork(session_factory)

    response = Response()
    payload = ReferralCreateRequest(referrer_telegram_id=10, referred_telegram_id=20)
    await create_referral(payload, response, build_uow())
    assert response.status_code == 201

    referrer_status = await get_user_status(10, build_uow())
    referred_status = await get_user_status(20, build_uow())

    assert referrer_status.telegram_id == 10
    assert referred_status.telegram_id == 20
    await engine.dispose()
