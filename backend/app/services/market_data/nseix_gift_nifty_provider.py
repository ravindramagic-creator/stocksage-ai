import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_data.base import MarketDataProvider


class NSEIXGiftNiftyProvider(MarketDataProvider):
    """Read the near-month GIFT NIFTY future from NSE International Exchange."""

    URLS = (
        "https://www.nseix.com/",
        "https://www1.nseix.com/",
    )

    LABELS = (
        "Intra Day Price - Near month GIFT NIFTY Future",
        "Near month GIFT NIFTY Future",
        "GIFT NIFTY Future",
    )

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )

    @staticmethod
    def _float(value: str | None) -> float | None:
        try:
            return (
                float(value.replace(",", ""))
                if value
                else None
            )
        except (TypeError, ValueError):
            return None

    def _parse(self, html: str) -> StockQuote | None:
        text = BeautifulSoup(
            html,
            "html.parser",
        ).get_text(
            " ",
            strip=True,
        )

        # NSE IX has changed whitespace/markup around this widget over time.
        # Search a bounded region after the label instead of requiring an
        # exact DOM layout.
        for label in self.LABELS:
            start = text.lower().find(label.lower())
            if start < 0:
                continue

            tail = text[start + len(label): start + len(label) + 500]

            match = re.search(
                r"([+-]?\d[\d,]*(?:\.\d+)?)\s+"
                r"([+-]?\d[\d,]*(?:\.\d+)?)\s*"
                r"\(([+-]?\d+(?:\.\d+)?)%\)",
                tail,
            )

            if not match:
                # Fallback for small markup changes between the price and
                # change fields.
                match = re.search(
                    r"([+-]?\d[\d,]*(?:\.\d+)?).*?"
                    r"([+-]?\d[\d,]*(?:\.\d+)?)\s*"
                    r"\(([+-]?\d+(?:\.\d+)?)%\)",
                    tail,
                )

            if not match:
                continue

            price = self._float(match.group(1))
            change = self._float(match.group(2))
            change_percent = self._float(match.group(3))

            if price is None:
                continue

            previous_close = (
                price - change
                if change is not None
                else None
            )

            return StockQuote(
                symbol="GIFT NIFTY",
                price=price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                currency="INR",
                market_state=None,
                updated_at=datetime.now(timezone.utc),
            )

        return None

    def get_quote(self, symbol: str) -> StockQuote | None:
        last_error: Exception | None = None

        for url in self.URLS:
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                quote = self._parse(response.text)
                if quote is not None:
                    return quote
            except requests.RequestException as exc:
                last_error = exc

        if last_error:
            raise last_error

        raise ValueError(
            "Unable to parse GIFT NIFTY from NSE IX"
        )

    def get_history(
        self,
        symbol: str,
        period: str,
        interval: str,
    ) -> HistoricalPrices:
        raise NotImplementedError(
            "NSE IX provider currently provides live GIFT NIFTY quotes only"
        )
