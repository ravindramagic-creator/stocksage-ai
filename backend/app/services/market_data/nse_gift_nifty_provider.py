import time
from datetime import datetime, timezone

import requests

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_data.base import MarketDataProvider


class NSEGiftniftyProvider(MarketDataProvider):
    """Read GIFT Nifty from NSE India's market-status feed."""

    URL = "https://www.nseindia.com/api/marketStatus"
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
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.nseindia.com/",
                "Connection": "keep-alive",
            }
        )

    @staticmethod
    def _float(value) -> float | None:
        try:
            return float(value) if value is not None else None
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

        self.session.get(
            "https://www.nseindia.com/",
            timeout=self.timeout,
        )

        response = self.session.get(
            self.URL,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        gift = payload.get("giftnifty") or {}

        price = self._float(gift.get("LASTPRICE"))
        change = self._float(gift.get("DAYCHANGE"))
        change_percent = self._float(gift.get("PERCHANGE"))

        if price is None:
            raise ValueError(
                "GIFT Nifty price is unavailable from NSE market-status feed"
            )

        previous_close = (
            price - change
            if change is not None
            else None
        )

        quote = StockQuote(
            symbol="GIFT NIFTY",
            price=price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            currency="INR",
            market_state="OPEN",
            updated_at=datetime.now(timezone.utc),
        )

        self.__class__._cached_quote = quote
        self.__class__._cached_at = now
        return quote

    def get_history(
        self,
        symbol: str,
        period: str,
        interval: str,
    ) -> HistoricalPrices:
        raise NotImplementedError(
            "NSE market-status provider currently provides live GIFT Nifty quotes only"
        )
