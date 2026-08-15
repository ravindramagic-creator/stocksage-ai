from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UpdateEventResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    symbol: str
    event_type: str
    priority: str
    title: str
    description: str | None
    source: str | None
    source_url: str | None
    old_value: float | None
    new_value: float | None
    event_time: datetime
    created_at: datetime
