from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_uow
from app.repositories.sqlalchemy import SqlAlchemyReferralRepository, SqlAlchemyUserRepository
from app.schemas import (
    ReferralCreateRequest,
    ReferralResponse,
    ReferralSummaryResponse,
    UserResponse,
    UserStatusResponse,
    UserUpsertRequest,
)
from app.usecases.errors import ConflictError, NotFoundError, ValidationError
from app.usecases.referrals import CreateReferral, GetReferralSummary
from app.usecases.users import GetUserStatus, UpsertUser

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users/upsert", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def upsert_user(
    payload: UserUpsertRequest,
    uow=Depends(get_uow),
):
    async with uow:
        users_repo = SqlAlchemyUserRepository(uow.session)
        usecase = UpsertUser(users_repo)
        try:
            user = await usecase.execute(payload.telegram_id)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return UserResponse(**user.__dict__)


@router.post("/referrals", response_model=ReferralResponse)
async def create_referral(
    payload: ReferralCreateRequest,
    response: Response,
    uow=Depends(get_uow),
):
    async with uow:
        referrals_repo = SqlAlchemyReferralRepository(uow.session)
        usecase = CreateReferral(referrals_repo)
        try:
            referral, created = await usecase.execute(
                payload.referrer_telegram_id, payload.referred_telegram_id
            )
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        logger.info("Referral processed", extra={"created": created})
        return ReferralResponse(**referral.__dict__)


@router.get(
    "/users/{telegram_id}/status",
    response_model=UserStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_status(
    telegram_id: int,
    uow=Depends(get_uow),
):
    async with uow:
        users_repo = SqlAlchemyUserRepository(uow.session)
        referrals_repo = SqlAlchemyReferralRepository(uow.session)
        usecase = GetUserStatus(users_repo, referrals_repo)
        try:
            status_data = await usecase.execute(telegram_id)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return UserStatusResponse(**status_data)


@router.get(
    "/referrals/{referrer_telegram_id}/summary",
    response_model=ReferralSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_referral_summary(
    referrer_telegram_id: int,
    uow=Depends(get_uow),
):
    async with uow:
        referrals_repo = SqlAlchemyReferralRepository(uow.session)
        usecase = GetReferralSummary(referrals_repo)
        try:
            summary = await usecase.execute(referrer_telegram_id)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ReferralSummaryResponse(**summary)
