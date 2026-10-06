from pydantic import BaseModel


class FundamentalAnalysisResponse(BaseModel):
    symbol: str
    company_name: str | None = None
    overall_score: float | None = None
    verdict: str
    data_completeness: float

    revenue_growth: float | None = None
    profit_growth: float | None = None
    eps_growth: float | None = None

    roe: float | None = None
    roce: float | None = None
    debt_to_equity: float | None = None

    pe: float | None = None
    peg: float | None = None
    pb: float | None = None

    analyst_beat_rate: float | None = None
    target_upside: float | None = None

    latest_revenue_yoy: float | None = None
    latest_pat_yoy: float | None = None
    latest_eps_yoy: float | None = None
    latest_result: str | None = None

    strengths: list[str]
    risks: list[str]
    summary: str
