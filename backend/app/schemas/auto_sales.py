from datetime import date
from pydantic import BaseModel, ConfigDict


class AutoSalesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    company_name: str
    segment: str
    month: date
    registrations: int | None = None
    domestic_sales: int | None = None
    export_sales: int | None = None
    total_sales: int | None = None
    yoy_growth: float | None = None
    mom_growth: float | None = None
    market_share: float | None = None
    data_type: str
    source: str
    source_url: str | None = None
    is_projected: bool


class AutoSalesSeriesPoint(BaseModel):
    month: date
    value: int | None = None
    yoy_growth: float | None = None
    mom_growth: float | None = None


class AutoSalesSeries(BaseModel):
    symbol: str
    company_name: str
    segment: str
    metric: str
    data: list[AutoSalesSeriesPoint]


class AutoSalesSummary(BaseModel):
    month: date
    total: int
    companies: int
    segments: int
