from datetime import datetime

from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str
    price: float | None = None
    previous_close: float | None = None
    open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    volume: int | None = None

    change: float | None = None
    change_percent: float | None = None

    currency: str | None = None

    market_state: str | None = None

    updated_at: datetime


class PricePoint(BaseModel):
    timestamp: datetime
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None


class HistoricalPrices(BaseModel):
    symbol: str
    interval: str
    points: list[PricePoint]
