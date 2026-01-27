from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.notifications.interfaces import TelegramNotifier
from app.repositories.interfaces import PriceSampleRepository

logger = logging.getLogger(__name__)


class PriceFetcher(Protocol):
    async def fetch(self, symbol: str, last_price: float | None) -> float:
        ...


@dataclass(frozen=True)
class PriceAlertResult:
    symbol: str
    price: float
    last_price: float | None
    change_ratio: float | None
    alerted: bool


class PriceAlertService:
    def __init__(
        self,
        price_samples: PriceSampleRepository,
        notifier: TelegramNotifier,
        fetcher: PriceFetcher,
        symbol: str,
        threshold: float = 0.01,
    ) -> None:
        self._price_samples = price_samples
        self._notifier = notifier
        self._fetcher = fetcher
        self._symbol = symbol
        self._threshold = threshold

    async def run_once(self) -> PriceAlertResult | None:
        try:
            last_sample = await self._price_samples.get_latest(self._symbol)
        except Exception:
            logger.exception("Failed to load last price sample symbol=%s", self._symbol)
            raise

        try:
            price = await self._fetcher.fetch(
                self._symbol, last_sample.price if last_sample else None
            )
        except Exception:
            logger.exception("Failed to fetch price symbol=%s", self._symbol)
            return None

        try:
            await self._price_samples.create(self._symbol, price)
        except Exception:
            logger.exception(
                "Failed to persist price sample symbol=%s price=%s", self._symbol, price
            )
            raise

        change_ratio: float | None = None
        alerted = False
        if last_sample and last_sample.price:
            change_ratio = abs(price - last_sample.price) / last_sample.price
            if change_ratio > self._threshold:
                message = (
                    f"Price alert for {self._symbol}: {price:.2f} "
                    f"({change_ratio * 100:.2f}% change)"
                )
                try:
                    await self._notifier.send_message(message)
                    alerted = True
                except Exception:
                    logger.exception(
                        "Failed to send alert symbol=%s change_ratio=%s",
                        self._symbol,
                        change_ratio,
                    )

        logger.info(
            "Price alert cycle symbol=%s price=%s last_price=%s change_ratio=%s alerted=%s",
            self._symbol,
            price,
            last_sample.price if last_sample else None,
            change_ratio,
            alerted,
        )
        return PriceAlertResult(
            symbol=self._symbol,
            price=price,
            last_price=last_sample.price if last_sample else None,
            change_ratio=change_ratio,
            alerted=alerted,
        )
