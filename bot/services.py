from __future__ import annotations

from app.db.session import UnitOfWork
from app.repositories.sqlalchemy import SqlAlchemyReferralRepository, SqlAlchemyUserRepository
from app.usecases.referrals import CreateReferral, GetReferralSummary
from app.usecases.users import GetUserStatus, UpsertUser


class BotService:
    def __init__(self, uow_factory: type[UnitOfWork] = UnitOfWork) -> None:
        self._uow_factory = uow_factory

    async def upsert_user(self, telegram_id: int):
        async with self._uow_factory() as uow:
            users_repo = SqlAlchemyUserRepository(uow.session)
            usecase = UpsertUser(users_repo)
            return await usecase.execute(telegram_id)

    async def register_user_and_referral(
        self, telegram_id: int, referrer_telegram_id: int | None
    ):
        async with self._uow_factory() as uow:
            users_repo = SqlAlchemyUserRepository(uow.session)
            referrals_repo = SqlAlchemyReferralRepository(uow.session)
            upsert_user = UpsertUser(users_repo)
            create_referral = CreateReferral(referrals_repo)
            await upsert_user.execute(telegram_id)
            if referrer_telegram_id:
                await upsert_user.execute(referrer_telegram_id)
                return await create_referral.execute(referrer_telegram_id, telegram_id)
            return None

    async def get_status(self, telegram_id: int):
        async with self._uow_factory() as uow:
            users_repo = SqlAlchemyUserRepository(uow.session)
            referrals_repo = SqlAlchemyReferralRepository(uow.session)
            usecase = GetUserStatus(users_repo, referrals_repo)
            return await usecase.execute(telegram_id)

    async def get_referral_summary(self, telegram_id: int):
        async with self._uow_factory() as uow:
            referrals_repo = SqlAlchemyReferralRepository(uow.session)
            usecase = GetReferralSummary(referrals_repo)
            return await usecase.execute(telegram_id)
