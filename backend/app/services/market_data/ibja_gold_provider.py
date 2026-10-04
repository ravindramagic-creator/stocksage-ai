import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_data.base import MarketDataProvider


class IBJAGoldProvider(MarketDataProvider):
    """Fetch India's benchmark 24K/999 gold rate in INR per 10 grams."""

    URL = "https://www.ibjarates.com/index.aspx"

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
        response = self.session.get(
            self.URL,
            timeout=self.timeout,
        )
        response.raise_for_status()

        text = BeautifulSoup(
            response.text,
            "html.parser",
        ).get_text(" ", strip=True)

        # The public IBJA page presents the latest Gold 999 AM/PM benchmark
        # as rupees per 10 grams. Prefer PM, falling back to AM on days when
        # the PM session is not available.
        match = re.search(
            r"Gold\s+999\s*\|\s*"
            r"([0-9,]+)\s*\|\s*"
            r"([0-9,]+)",
            text,
            re.IGNORECASE,
        )
        if not match:
            # Table extraction can collapse separators depending on markup.
            match = re.search(
                r"Gold\s+999.*?"
                r"([0-9]{5,6})\s+([0-9]{5,6})",
                text,
                re.IGNORECASE,
            )

        if not match:
            # Latest 999 value shown in the page's large "1 Gram" card.
            match = re.search(
                r"999\s+Purity\s+([0-9,]+)\s*\(1\s*Gram\)",
                text,
                re.IGNORECASE,
            )
            if match:
                per_gram = self._float(match.group(1))
                if per_gram is not None:
                    return self._quote(
                        per_gram * 10,
                        None,
                    )

            raise ValueError("Unable to parse IBJA Gold 999 rate")

        am = self._float(match.group(1))
        pm = self._float(match.group(2))
        price = pm or am

        if price is None:
            raise ValueError("IBJA Gold 999 rate is unavailable")

        change_percent = None
        # The page includes recent PM/AM history below the current row. A
        # simple previous PM comparison gives a useful benchmark change.
        history_match = re.search(
            r"Gold\s+999\s*\|\s*"
            r"[0-9,]+\s*\|\s*[0-9,]+.*?"
            r"Previous\s+Dates\s+Rate",
            text,
            re.IGNORECASE,
        )
        _ = history_match  # Retain parsing focused on the benchmark price.

        return self._quote(
            price,
            change_percent,
        )

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
