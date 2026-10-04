from pydantic import BaseModel, Field


class ScreenerResult(BaseModel):
    rank: int
    symbol: str
    company_name: str
    sector: str | None = None

    score: float
    verdict: str

    price: float | None = None
    market_cap: float | None = None
    pe: float | None = None
    pb: float | None = None
    roe: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    profit_growth: float | None = None
    eps_growth: float | None = None
    target_upside: float | None = None

    quality_score: float | None = None
    growth_score: float | None = None
    valuation_score: float | None = None
    momentum_score: float | None = None
    analyst_score: float | None = None


class ScreenerResponse(BaseModel):
    total_universe: int
    screened: int
    results: list[ScreenerResult]
    data_source: str
    methodology: str


class ScreenerFilters(BaseModel):
    min_score: float = Field(default=60, ge=0, le=100)
    min_roe: float = Field(default=15, ge=-100, le=200)
    max_pe: float = Field(default=45, ge=0, le=500)
    max_debt_to_equity: float = Field(default=1.0, ge=0, le=20)
    min_revenue_growth: float = Field(default=10, ge=-100, le=500)
    min_profit_growth: float = Field(default=10, ge=-100, le=500)
    min_market_cap: float = Field(default=5000, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    universe_limit: int = Field(default=250, ge=20, le=1000)
