from functools import lru_cache

from app.services.market_data.base import (
    MarketDataProvider,
)
from app.services.market_data.yfinance_provider import (
    YFinanceProvider,
)


@lru_cache(maxsize=1)
def get_market_data_provider() -> MarketDataProvider:
    return YFinanceProvider()
