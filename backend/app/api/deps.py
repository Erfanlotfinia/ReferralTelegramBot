from __future__ import annotations

from app.db.session import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork()
