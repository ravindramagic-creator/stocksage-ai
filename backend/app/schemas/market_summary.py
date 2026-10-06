from datetime import datetime

from pydantic import BaseModel


class MarketSummaryResponse(BaseModel):
    as_of: datetime
    headline: str
    regime: str
    regime_score: int

    nifty: float | None = None
    nifty_change_percent: float | None = None
    bank_nifty: float | None = None
    bank_nifty_change_percent: float | None = None
    midcap: float | None = None
    midcap_change_percent: float | None = None
    smallcap: float | None = None
    smallcap_change_percent: float | None = None
    india_vix: float | None = None
    india_vix_change_percent: float | None = None
    brent: float | None = None
    brent_change_percent: float | None = None
    usd_inr: float | None = None
    usd_inr_change_percent: float | None = None

    breadth_above_50dma_pct: float | None = None
    positive_indices: list[str]
    negative_indices: list[str]

    key_points: list[str]
    investor_takeaway: str
