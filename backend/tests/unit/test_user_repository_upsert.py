from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.sqlalchemy import SqlAlchemyUserRepository


@dataclass
class FakeUser:
    id: int
    telegram_id: int
    created_at: datetime


class FakeResult:
    def __init__(self, user: FakeUser | None) -> None:
        self._user = user

    def scalar_one_or_none(self) -> FakeUser | None:
        return self._user


class FakeSession:
    def __init__(self, first_user: FakeUser | None, after_user: FakeUser | None) -> None:
        self._first_user = first_user
        self._after_user = after_user
        self._execute_calls = 0
        self.rolled_back = False
        self.begin_nested_called = False
        self.added = []

    async def execute(self, *args, **kwargs) -> FakeResult:
        self._execute_calls += 1
        user = self._first_user if self._execute_calls == 1 else self._after_user
        return FakeResult(user)

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        raise IntegrityError("insert", {}, Exception("duplicate"))

    def expunge(self, obj) -> None:
        self.added.remove(obj)

    async def rollback(self) -> None:
        self.rolled_back = True

    class _BeginNested:
        def __init__(self, session: "FakeSession") -> None:
            self._session = session

        async def __aenter__(self) -> None:
            self._session.begin_nested_called = True

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    def begin_nested(self) -> _BeginNested:
        return self._BeginNested(self)

    class _NoAutoflush:
        def __enter__(self) -> None:
            return None

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

    @property
    def no_autoflush(self) -> _NoAutoflush:
        return self._NoAutoflush()

@pytest.mark.asyncio
async def test_upsert_user_handles_integrity_error() -> None:
    existing = FakeUser(
        id=1, telegram_id=42, created_at=datetime.now(timezone.utc)
    )
    session = FakeSession(first_user=None, after_user=existing)
    repo = SqlAlchemyUserRepository(session)

    record = await repo.upsert(42)

    assert record.telegram_id == 42
    assert record.id == 1
    assert session.begin_nested_called is True
    assert session.rolled_back is False
