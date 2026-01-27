from __future__ import annotations

import asyncio
import logging
import os

import aiohttp

from app.core.logging import setup_logging
from app.db.session import UnitOfWork
from app.repositories.sqlalchemy import SqlAlchemyPriceSampleRepository
from app.usecases.price_alerts import PriceAlertService
from app.worker.price_fetcher import ApiPriceFetcher
from app.worker.telegram_notifier import AiogramTelegramNotifier, NullTelegramNotifier

logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s=%s; using default=%s", name, value, default)
        return default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid int for %s=%s; using default=%s", name, value, default)
        return default


async def _run_worker() -> None:
    setup_logging()
    interval = _env_int("PRICE_ALERT_INTERVAL_SECONDS", 300)
    threshold = _env_float("PRICE_ALERT_THRESHOLD", 0.01)
    symbol = os.getenv("PRICE_ALERT_SYMBOL", "BTC-USD")
    api_url = os.getenv(
        "PRICE_ALERT_API_URL", "https://api.coinbase.com/v2/prices/{symbol}/spot"
    )
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ALERT_CHAT_ID")

    notifier = (
        AiogramTelegramNotifier(token, chat_id)
        if token and chat_id
        else NullTelegramNotifier()
    )
    if not (token and chat_id):
        logger.warning("Telegram alert env vars missing; alerts will be logged only")

    async with aiohttp.ClientSession() as session:
        fetcher = ApiPriceFetcher(api_url, session)
        while True:
            try:
                async with UnitOfWork() as uow:
                    repo = SqlAlchemyPriceSampleRepository(uow.session)
                    service = PriceAlertService(
                        price_samples=repo,
                        notifier=notifier,
                        fetcher=fetcher,
                        symbol=symbol,
                        threshold=threshold,
                    )
                    await service.run_once()
            except Exception:
                logger.exception("Price alert worker cycle failed")
            await asyncio.sleep(interval)


def main() -> None:
    asyncio.run(_run_worker())


if __name__ == "__main__":
    main()
