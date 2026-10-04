from datetime import datetime, timezone

import requests

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_data.base import MarketDataProvider


class NSEQuoteProvider(MarketDataProvider):
    """Lightweight fallback for live NSE equity quotes.

    This provider is intentionally quote-only. Historical OHLCV remains on
    the existing Yahoo provider because the NSE historical API has different
    pagination/date semantics.
    """

    URL = "https://www.nseindia.com/api/quote-equity"

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
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.nseindia.com/",
                "Connection": "keep-alive",
            }
        )

    @staticmethod
    def _float(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int(value):
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = symbol.upper().replace(".NS", "")

        # Establish NSE cookies first. NSE occasionally returns an HTML page
        # when this bootstrap is skipped, which otherwise looks like a JSON
        # parsing failure.
        self.session.get("https://www.nseindia.com/", timeout=self.timeout)
        response = self.session.get(
            self.URL,
            params={"symbol": symbol},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()

        price_info = payload.get("priceInfo") or {}
        intra_day = price_info.get("intraDayHighLow") or {}
        info = payload.get("info") or {}
        security = payload.get("securityInfo") or {}
        trade_info = (payload.get("marketDeptOrderBook") or {}).get("tradeInfo") or {}

        price = self._float(price_info.get("lastPrice"))
        previous_close = self._float(price_info.get("previousClose"))
        open_price = self._float(price_info.get("open"))
        day_high = self._float(intra_day.get("max"))
        day_low = self._float(intra_day.get("min"))
        volume = self._int(trade_info.get("totalTradedVolume"))

        change = None
        change_percent = None
        if price is not None and previous_close not in (None, 0):
            change = price - previous_close
            change_percent = (change / previous_close) * 100

        return StockQuote(
            symbol=symbol,
            price=price,
            previous_close=previous_close,
            open=open_price,
            day_high=day_high,
            day_low=day_low,
            volume=volume,
            change=change,
            change_percent=change_percent,
            currency="INR",
            market_state=security.get("tradingStatus") or info.get("tradingStatus"),
            updated_at=datetime.now(timezone.utc),
        )

    def get_history(self, symbol: str, period: str, interval: str) -> HistoricalPrices:
        raise NotImplementedError("NSE fallback currently provides live quotes only")
