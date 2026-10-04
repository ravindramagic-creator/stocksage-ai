import time
from functools import lru_cache

import yfinance.exceptions as yf_exceptions

from app.services.market_data.base import MarketDataProvider
from app.services.market_data.nse_quote_provider import NSEQuoteProvider
from app.services.market_data.yfinance_provider import YFinanceProvider


class ResilientMarketDataProvider(MarketDataProvider):
    """Use Yahoo normally, but fail over safely when Yahoo/NSE are unavailable."""

    YAHOO_COOLDOWN_SECONDS = 300

    def __init__(self):
        self.yahoo = YFinanceProvider()
        self.nse = NSEQuoteProvider()
        self._yahoo_disabled_until = 0.0

    def _yahoo_available(self) -> bool:
        return time.monotonic() >= self._yahoo_disabled_until

    def _disable_yahoo(self) -> None:
        self._yahoo_disabled_until = time.monotonic() + self.YAHOO_COOLDOWN_SECONDS

    def get_quote(self, symbol: str):
        if not self._yahoo_available():
            try:
                return self.nse.get_quote(symbol)
            except Exception:
                # During an upstream outage, don't turn a cached/background
                # update failure into a 500/502 for the whole worker.
                return None

        try:
            return self.yahoo.get_quote(symbol)
        except yf_exceptions.YFRateLimitError:
            self._disable_yahoo()
        except Exception:
            pass

        try:
            return self.nse.get_quote(symbol)
        except Exception:
            return None

    def get_history(self, symbol: str, period: str, interval: str):
        return self.yahoo.get_history(symbol, period, interval)


@lru_cache(maxsize=1)
def get_market_data_provider() -> MarketDataProvider:
    return ResilientMarketDataProvider()
