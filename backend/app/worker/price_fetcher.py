from __future__ import annotations

import logging
import random
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class ApiPriceFetcher:
    def __init__(self, api_url_template: str, session: aiohttp.ClientSession) -> None:
        self._api_url_template = api_url_template
        self._session = session

    async def fetch(self, symbol: str, last_price: float | None) -> float:
        url = self._api_url_template.format(symbol=symbol)
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                payload: dict[str, Any] = await resp.json()
            price = self._parse_price(payload)
            if price <= 0:
                raise ValueError("price must be positive")
            return price
        except Exception:
            logger.warning("Falling back to mock price symbol=%s", symbol, exc_info=True)
            return self._mock_price(last_price)

    @staticmethod
    def _parse_price(payload: dict[str, Any]) -> float:
        data = payload.get("data", {})
        amount = data.get("amount")
        if amount is None:
            raise ValueError("missing amount in response")
        return float(amount)

    @staticmethod
    def _mock_price(last_price: float | None) -> float:
        base = last_price if last_price and last_price > 0 else 100.0
        delta = random.uniform(-0.005, 0.005)
        return round(base * (1 + delta), 4)
