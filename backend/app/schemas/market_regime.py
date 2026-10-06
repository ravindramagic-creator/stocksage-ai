from pydantic import BaseModel


class MarketRegimeFactor(BaseModel):
    name: str
    status: str
    detail: str


class MarketRegimeResponse(BaseModel):
    regime: str
    score: int
    bullish_signals: int
    bearish_signals: int
    neutral_signals: int

    nifty: float | None = None
    nifty_50dma: float | None = None
    nifty_200dma: float | None = None
    nifty_rsi: float | None = None
    nifty_momentum_6m: float | None = None
    india_vix: float | None = None
    breadth_above_50dma_pct: float | None = None

    factors: list[MarketRegimeFactor]
    note: str
