from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Referral, User


async def _build_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return session_factory()


@pytest.mark.asyncio
async def test_users_unique_telegram_id() -> None:
    session = await _build_session()
    session.add(User(telegram_id=101))
    await session.commit()
    session.add(User(telegram_id=101))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    await session.close()


@pytest.mark.asyncio
async def test_referrals_unique_referred() -> None:
    session = await _build_session()
    session.add(Referral(referrer_telegram_id=1, referred_telegram_id=2))
    await session.commit()
    session.add(Referral(referrer_telegram_id=3, referred_telegram_id=2))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    await session.close()


@pytest.mark.asyncio
async def test_referrals_block_self_referral() -> None:
    session = await _build_session()
    session.add(Referral(referrer_telegram_id=5, referred_telegram_id=5))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    await session.close()
