from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FinancialResultResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id: int

    symbol: str

    company_name: str | None

    # ---------------------------------------------------------
    # Period
    # ---------------------------------------------------------

    period_ended: date | None

    period_type: str | None

    consolidated: bool

    # ---------------------------------------------------------
    # Revenue
    # ---------------------------------------------------------

    revenue: Decimal | None

    revenue_yoy: Decimal | None

    revenue_qoq: Decimal | None

    # Analyst estimate
    revenue_estimate: Decimal | None

    # Actual vs estimate
    revenue_surprise_pct: Decimal | None

    # BEAT / MISS / MEET / UNKNOWN
    revenue_result: str | None

    # ---------------------------------------------------------
    # EBITDA
    # ---------------------------------------------------------

    ebitda: Decimal | None

    ebitda_yoy: Decimal | None

    ebitda_qoq: Decimal | None

    # Analyst estimate
    ebitda_estimate: Decimal | None

    # Actual vs estimate
    ebitda_surprise_pct: Decimal | None

    # BEAT / MISS / MEET / UNKNOWN
    ebitda_result: str | None

    # ---------------------------------------------------------
    # PAT / Net Profit
    # ---------------------------------------------------------

    pat: Decimal | None

    pat_yoy: Decimal | None

    pat_qoq: Decimal | None

    # Analyst estimate
    pat_estimate: Decimal | None

    # Actual vs estimate
    pat_surprise_pct: Decimal | None

    # BEAT / MISS / MEET / UNKNOWN
    pat_result: str | None

    # ---------------------------------------------------------
    # EPS
    # ---------------------------------------------------------

    eps: Decimal | None

    eps_yoy: Decimal | None

    # Analyst estimate
    eps_estimate: Decimal | None

    # Actual vs estimate
    eps_surprise_pct: Decimal | None

    # BEAT / MISS / MEET / UNKNOWN
    eps_result: str | None

    # ---------------------------------------------------------
    # Overall result
    # ---------------------------------------------------------

    # BEAT / MISS / MEET / UNKNOWN
    overall_result: str | None

    # ---------------------------------------------------------
    # Market view
    # ---------------------------------------------------------

    market_view: str | None

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary: str | None

    # ---------------------------------------------------------
    # Source
    # ---------------------------------------------------------

    source: str | None

    source_url: str | None

    broadcast_date: datetime | None

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_at: datetime
