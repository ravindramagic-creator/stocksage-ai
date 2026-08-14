from pydantic import BaseModel

from app.schemas.stock import StockResponse


class WatchlistCreate(BaseModel):
    symbol: str


class WatchlistResponse(BaseModel):
    id: int
    stock: StockResponse
