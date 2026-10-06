from datetime import datetime

from pydantic import BaseModel


class MarketNewsItemResponse(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime
    category: str
    importance: str
