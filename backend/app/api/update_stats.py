from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.update_event import UpdateEvent


router = APIRouter(
    prefix="/updates",
    tags=["Updates"],
)


@router.get("/stats")
def get_update_stats(
    db: Session = Depends(get_db),
):

    statement = (
        select(
            UpdateEvent.event_type,
            func.count(UpdateEvent.id),
        )
        .group_by(
            UpdateEvent.event_type
        )
        .order_by(
            func.count(UpdateEvent.id).desc()
        )
    )

    rows = db.execute(
        statement
    ).all()

    return {
        "total": sum(
            count
            for _, count in rows
        ),
        "by_type": {
            event_type: count
            for event_type, count in rows
        },
    }
