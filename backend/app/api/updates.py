from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.update_event import (
    UpdateEventResponse,
)
from app.services.update_service import (
    UpdateService,
)


router = APIRouter(
    prefix="/updates",
    tags=["Updates"],
)

@router.get(
    "",
    response_model=list[
        UpdateEventResponse
    ],
)
def get_updates(
    limit: int = 50,
    symbol: str | None = None,
    event_type: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
):

    service = UpdateService(db)

    return service.get_recent(
        limit=limit,
        symbol=symbol,
        event_type=event_type,
        priority=priority,
    )
