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

    revenue: Decimal | None
    revenue_yoy: Decimal | None
    revenue_qoq: Decimal | None

    ebitda: Decimal | None
    ebitda_yoy: Decimal | None
    ebitda_qoq: Decimal | None

    pat: Decimal | None
    pat_yoy: Decimal | None
    pat_qoq: Decimal | None

    eps: Decimal | None
    eps_yoy: Decimal | None

    market_view: str | None

    summary: str | None

    source: str | None
    source_url: str | None

    broadcast_date: datetime | None

    created_at: datetime
