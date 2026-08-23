from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FinancialResultResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    symbol: str

    company_name: str | None

    period_ended: date | None

    period_type: str | None

    consolidated: bool

    # Revenue

    revenue: Decimal | None
    revenue_yoy: Decimal | None
    revenue_qoq: Decimal | None

    revenue_estimate: Decimal | None
    revenue_surprise_pct: Decimal | None
    revenue_result: str | None

    # EBITDA

    ebitda: Decimal | None
    ebitda_yoy: Decimal | None
    ebitda_qoq: Decimal | None

    ebitda_estimate: Decimal | None
    ebitda_surprise_pct: Decimal | None
    ebitda_result: str | None

    # PAT

    pat: Decimal | None
    pat_yoy: Decimal | None
    pat_qoq: Decimal | None

    pat_estimate: Decimal | None
    pat_surprise_pct: Decimal | None
    pat_result: str | None

    # EPS

    eps: Decimal | None
    eps_yoy: Decimal | None

    eps_estimate: Decimal | None
    eps_surprise_pct: Decimal | None
    eps_result: str | None

    # Overall

    overall_result: str | None

    market_view: str | None

    summary: str | None

    source: str | None
    source_url: str | None

    broadcast_date: datetime | None

    created_at: datetime
