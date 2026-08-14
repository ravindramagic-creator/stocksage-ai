from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.stock import StockResponse


class SubscriptionCreate(BaseModel):
    symbol: str
    company_name: str | None = None
    exchange: str = "NSE"
    sector: str | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    stock: StockResponse
