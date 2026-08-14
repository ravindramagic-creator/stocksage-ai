from datetime import datetime, timezone

import yfinance as yf

from app.schemas.market_data import (
    HistoricalPrices,
    PricePoint,
    StockQuote,
)
from app.services.market_data.base import (
    MarketDataProvider,
)


class YFinanceProvider(MarketDataProvider):

    @staticmethod
    def _ticker_symbol(symbol: str) -> str:
        return f"{symbol.upper()}.NS"

    def get_quote(self, symbol: str) -> StockQuote:
        normalized_symbol = symbol.upper()

        ticker = yf.Ticker(
            self._ticker_symbol(normalized_symbol)
        )

        fast_info = ticker.fast_info

        price = self._safe_float(
            fast_info.get("lastPrice")
        )

        previous_close = self._safe_float(
            fast_info.get("previousClose")
        )

        open_price = self._safe_float(
            fast_info.get("open")
        )

        day_high = self._safe_float(
            fast_info.get("dayHigh")
        )

        day_low = self._safe_float(
            fast_info.get("dayLow")
        )

        volume = self._safe_int(
            fast_info.get("lastVolume")
        )

        change = None
        change_percent = None

        if price is not None and previous_close:
            change = price - previous_close

            change_percent = (
                change / previous_close
            ) * 100

        return StockQuote(
            symbol=normalized_symbol,
            price=price,
            previous_close=previous_close,
            open=open_price,
            day_high=day_high,
            day_low=day_low,
            volume=volume,
            change=change,
            change_percent=change_percent,
            currency="INR",
            updated_at=datetime.now(
                timezone.utc
            ),
        )

    def get_history(
        self,
        symbol: str,
        period: str,
        interval: str,
    ) -> HistoricalPrices:

        normalized_symbol = symbol.upper()

        ticker = yf.Ticker(
            self._ticker_symbol(normalized_symbol)
        )

        history = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
        )

        points: list[PricePoint] = []

        for timestamp, row in history.iterrows():

            timestamp_value = timestamp.to_pydatetime()

            if timestamp_value.tzinfo is None:
                timestamp_value = timestamp_value.replace(
                    tzinfo=timezone.utc
                )

            points.append(
                PricePoint(
                    timestamp=timestamp_value,
                    open=self._safe_float(
                        row.get("Open")
                    ),
                    high=self._safe_float(
                        row.get("High")
                    ),
                    low=self._safe_float(
                        row.get("Low")
                    ),
                    close=self._safe_float(
                        row.get("Close")
                    ),
                    volume=self._safe_int(
                        row.get("Volume")
                    ),
                )
            )

        return HistoricalPrices(
            symbol=normalized_symbol,
            interval=interval,
            points=points,
        )

    @staticmethod
    def _safe_float(value) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
