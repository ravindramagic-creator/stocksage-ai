import time
from functools import lru_cache

import yfinance.exceptions as yf_exceptions

from app.services.market_data.base import MarketDataProvider
from app.services.market_data.nse_quote_provider import NSEQuoteProvider
from app.services.market_data.yfinance_provider import YFinanceProvider


class ResilientMarketDataProvider(MarketDataProvider):
    """Use Yahoo normally, but fail over to NSE when Yahoo is throttled."""

    YAHOO_COOLDOWN_SECONDS = 300

    def __init__(self):
        self.yahoo = YFinanceProvider()
        self.nse = NSEQuoteProvider()
        self._yahoo_disabled_until = 0.0

    def _yahoo_available(self) -> bool:
        return time.monotonic() >= self._yahoo_disabled_until

    def _disable_yahoo(self) -> None:
        self._yahoo_disabled_until = (
            time.monotonic() + self.YAHOO_COOLDOWN_SECONDS
        )

    def get_quote(self, symbol: str):
        # Once Yahoo has returned a 429, don't hammer it again for every stock
        # rendered by the dashboard. All quote requests use NSE during the
        # cooldown window.
        if not self._yahoo_available():
            return self.nse.get_quote(symbol)

        try:
            return self.yahoo.get_quote(symbol)
        except yf_exceptions.YFRateLimitError:
            self._disable_yahoo()
            return self.nse.get_quote(symbol)
        except Exception:
            # Other transient Yahoo failures also get a single NSE fallback,
            # but do not disable Yahoo globally because they may be symbol-specific.
            return self.nse.get_quote(symbol)

    def get_history(self, symbol: str, period: str, interval: str):
        # Historical charts/technical indicators remain on Yahoo. The NSE
        # fallback currently implements live quotes only.
        return self.yahoo.get_history(symbol, period, interval)


@lru_cache(maxsize=1)
def get_market_data_provider() -> MarketDataProvider:
    return ResilientMarketDataProvider()
