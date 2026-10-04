from functools import lru_cache

from app.services.market_data.base import MarketDataProvider
from app.services.market_data.nse_quote_provider import NSEQuoteProvider
from app.services.market_data.yfinance_provider import YFinanceProvider


class ResilientMarketDataProvider(MarketDataProvider):
    """Use Yahoo as the primary source and NSE as a live-quote fallback."""

    def __init__(self):
        self.yahoo = YFinanceProvider()
        self.nse = NSEQuoteProvider()

    def get_quote(self, symbol: str):
        try:
            return self.yahoo.get_quote(symbol)
        except Exception:
            # Yahoo can temporarily return YFRateLimitError (HTTP 429). Do not
            # make the UI fail just because the primary provider is throttled.
            return self.nse.get_quote(symbol)

    def get_history(self, symbol: str, period: str, interval: str):
        # Historical charts and technical indicators continue using Yahoo.
        return self.yahoo.get_history(symbol, period, interval)


@lru_cache(maxsize=1)
def get_market_data_provider() -> MarketDataProvider:
    return ResilientMarketDataProvider()
