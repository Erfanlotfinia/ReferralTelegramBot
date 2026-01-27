from __future__ import annotations

import logging
import re
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.logging import set_request_id
from app.usecases.errors import ConflictError, NotFoundError, ValidationError
from bot.services import BotService

logger = logging.getLogger(__name__)

START_PAYLOAD_PATTERN = re.compile(r"^ref_(\d+)$", re.IGNORECASE)


def _parse_start_payload(text: str | None) -> tuple[int | None, str | None]:
    if not text:
        return None, None
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    payload = parts[1].strip()
    if not payload:
        return None, None
    match = START_PAYLOAD_PATTERN.match(payload)
    if not match:
        return None, "Invalid referral code. Use /start ref_12345."
    referrer_id = int(match.group(1))
    if referrer_id <= 0:
        return None, "Invalid referral code. Use /start ref_12345."
    return referrer_id, None


def _format_datetime(value: datetime | None) -> str:
    if not value:
        return "unknown"
    return value.isoformat(timespec="seconds")


def build_router(service: BotService) -> Router:
    router = Router()

    @router.message(Command("start"))
    async def start_handler(message: Message) -> None:
        set_request_id(str(message.message_id))
        telegram_id = message.from_user.id if message.from_user else None
        if not telegram_id:
            await message.answer("Sorry, I couldn't read your Telegram ID.")
            return

        referrer_id, error = _parse_start_payload(message.text)
        try:
            result = await service.register_user_and_referral(telegram_id, referrer_id)
        except ValidationError as exc:
            logger.warning("Validation error on /start", exc_info=exc)
            await message.answer("That referral code is not valid.")
            return
        except ConflictError:
            await message.answer(
                "You already have a referrer. If you think this is wrong, contact support."
            )
            return
        except Exception:
            logger.exception("Unexpected error on /start")
            await message.answer("Sorry, something went wrong. Please try again later.")
            return

        if error:
            await message.answer(
                "Welcome! If you meant to use a referral link, send /start ref_12345."
            )
            return

        if not referrer_id:
            await message.answer("Welcome! You are registered.")
            return

        if result:
            _, created = result
            if created:
                await message.answer("Referral registered successfully. Welcome!")
                return
            await message.answer("You're already referred by this user. Welcome back!")
            return

        await message.answer("Welcome! You are registered.")

    @router.message(Command("my_status"))
    async def my_status_handler(message: Message) -> None:
        set_request_id(str(message.message_id))
        telegram_id = message.from_user.id if message.from_user else None
        if not telegram_id:
            await message.answer("Sorry, I couldn't read your Telegram ID.")
            return
        try:
            status = await service.get_status(telegram_id)
        except NotFoundError:
            await message.answer("You are not registered yet. Send /start to begin.")
            return
        except ValidationError:
            await message.answer("Sorry, I couldn't process your request.")
            return
        except Exception:
            logger.exception("Unexpected error on /my_status")
            await message.answer("Sorry, something went wrong. Please try again later.")
            return

        referrer_id = status.get("referred_by") or "none"
        created_at = _format_datetime(status.get("created_at"))
        await message.answer(
            "Your status:\n"
            f"- Telegram ID: {status['telegram_id']}\n"
            f"- Referrer: {referrer_id}\n"
            f"- Created at: {created_at}"
        )

    @router.message(Command("ref_summary"))
    async def ref_summary_handler(message: Message) -> None:
        set_request_id(str(message.message_id))
        telegram_id = message.from_user.id if message.from_user else None
        if not telegram_id:
            await message.answer("Sorry, I couldn't read your Telegram ID.")
            return
        try:
            summary = await service.get_referral_summary(telegram_id)
        except ValidationError:
            await message.answer("Sorry, I couldn't process your request.")
            return
        except Exception:
            logger.exception("Unexpected error on /ref_summary")
            await message.answer("Sorry, something went wrong. Please try again later.")
            return

        if summary["count"] <= 0:
            await message.answer("You have no referrals yet.")
            return

        lines = [
            f"Total referrals: {summary['count']}",
            "Last 5 referrals:",
        ]
        for referral in summary["last_5_referrals"]:
            lines.append(
                f"- {referral['referred_telegram_id']} at "
                f"{_format_datetime(referral['created_at'])}"
            )
        await message.answer("\n".join(lines))

    return router
