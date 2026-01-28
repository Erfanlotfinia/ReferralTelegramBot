from __future__ import annotations

from collections.abc import AsyncIterator

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DATABASE_URL
from app.usecases.errors import DatabaseConnectionError

logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionFactory) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        try:
            await self.session.begin()
        except (OSError, SQLAlchemyError) as exc:
            logger.exception("Failed to open database session")
            await self.session.close()
            self.session = None
            raise DatabaseConnectionError("Database connection failed") from exc
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if not self.session:
            return
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()
