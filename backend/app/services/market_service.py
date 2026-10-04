from functools import lru_cache

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_cache import market_cache
from app.services.market_data.factory import get_market_data_provider


class MarketService:
    # Quotes are deliberately cached longer than before. The home page can
    # render many stocks at once; repeatedly requesting every quote from an
    # upstream provider is a common cause of rate limiting.
    QUOTE_TTL = 60
    HISTORY_TTL = 300

    def __init__(self):
        self.provider = get_market_data_provider()

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = symbol.strip().upper()
        cache_key = f"quote:{symbol}"

        cached = market_cache.get(cache_key)
        if cached is not None:
            return cached

        quote = self.provider.get_quote(symbol)
        market_cache.set(cache_key, quote, self.QUOTE_TTL)
        return quote

    def get_history(self, symbol: str, period: str, interval: str) -> HistoricalPrices:
        symbol = symbol.strip().upper()
        cache_key = f"history:{symbol}:{period}:{interval}"

        cached = market_cache.get(cache_key)
        if cached is not None:
            return cached

        history = self.provider.get_history(
            symbol=symbol,
            period=period,
            interval=interval,
        )
        market_cache.set(cache_key, history, self.HISTORY_TTL)
        return history


@lru_cache(maxsize=1)
def get_market_service() -> MarketService:
    return MarketService()
