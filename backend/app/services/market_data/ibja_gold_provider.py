import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_data.base import MarketDataProvider


class IBJAGoldProvider(MarketDataProvider):
    """Fetch India's benchmark 24K/999 gold rate in INR per 10 grams."""

    URL = "https://www.ibjarates.com/index.aspx"
    CACHE_TTL_SECONDS = 60
    _cached_quote: StockQuote | None = None
    _cached_at: float = 0.0

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.0"
                ),
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    @staticmethod
    def _float(value: str) -> float | None:
        try:
            return float(value.replace(",", "")) if value else None
        except (TypeError, ValueError):
            return None

    def get_quote(self, symbol: str) -> StockQuote:
        now = time.monotonic()
        cached = self.__class__._cached_quote
        if (
            cached is not None
            and now - self.__class__._cached_at < self.CACHE_TTL_SECONDS
        ):
            return cached

        response = self.session.get(
            self.URL,
            timeout=self.timeout,
        )
        response.raise_for_status()

        text = BeautifulSoup(
            response.text,
            "html.parser",
        ).get_text(" ", strip=True)

        match = re.search(
            r"Gold\s+999\s*\|\s*"
            r"([0-9,]+)\s*\|\s*"
            r"([0-9,]+)",
            text,
            re.IGNORECASE,
        )

        if not match:
            match = re.search(
                r"Gold\s+999.*?"
                r"([0-9]{5,6})\s+([0-9]{5,6})",
                text,
                re.IGNORECASE,
            )

        if not match:
            match = re.search(
                r"999\s+Purity\s+([0-9,]+)\s*\(1\s*Gram\)",
                text,
                re.IGNORECASE,
            )
            if match:
                per_gram = self._float(match.group(1))
                if per_gram is not None:
                    quote = self._quote(per_gram * 10, None)
                    self.__class__._cached_quote = quote
                    self.__class__._cached_at = now
                    return quote

            raise ValueError("Unable to parse IBJA Gold 999 rate")

        am = self._float(match.group(1))
        pm = self._float(match.group(2))
        price = pm or am

        if price is None:
            raise ValueError("IBJA Gold 999 rate is unavailable")

        quote = self._quote(price, None)
        self.__class__._cached_quote = quote
        self.__class__._cached_at = now
        return quote

    @staticmethod
    def _quote(
        price: float,
        change_percent: float | None,
    ) -> StockQuote:
        change = (
            price * change_percent / 100
            if change_percent is not None
            else None
        )
        previous_close = (
            price - change
            if change is not None
            else None
        )

        return StockQuote(
            symbol="GOLD",
            price=price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            currency="INR",
            market_state=None,
            updated_at=datetime.now(timezone.utc),
        )

    def get_history(
        self,
        symbol: str,
        period: str,
        interval: str,
    ) -> HistoricalPrices:
        raise NotImplementedError(
            "IBJA provider currently provides the latest benchmark rate only"
        )
