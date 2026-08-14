from abc import ABC, abstractmethod

from app.schemas.market_data import (
    HistoricalPrices,
    StockQuote,
)


class MarketDataProvider(ABC):

    @abstractmethod
    def get_quote(self, symbol: str) -> StockQuote:
        """Return the latest available quote."""
        raise NotImplementedError

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        period: str,
        interval: str,
    ) -> HistoricalPrices:
        """Return historical OHLCV data."""
        raise NotImplementedError
