from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.update_event import UpdateEvent


class UpdateEventRepository:

    def __init__(self, db: Session):
        self.db = db

    def exists(
        self,
        event_key: str,
    ) -> bool:

        statement = (
            select(UpdateEvent.id)
            .where(
                UpdateEvent.event_key
                == event_key
            )
            .limit(1)
        )

        return (
            self.db.execute(statement)
            .scalar_one_or_none()
            is not None
        )

    def create(
        self,
        *,
        symbol: str,
        event_type: str,
        priority: str,
        title: str,
        description: str | None,
        source: str | None,
        source_url: str | None,
        old_value: float | None,
        new_value: float | None,
        event_key: str,
        event_time: datetime,
    ) -> UpdateEvent:

        event = UpdateEvent(
            symbol=symbol.upper(),
            event_type=event_type,
            priority=priority,
            title=title,
            description=description,
            source=source,
            source_url=source_url,
            old_value=old_value,
            new_value=new_value,
            event_key=event_key,
            event_time=event_time,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def get_recent(
        self,
        limit: int = 50,
        symbol: str | None = None,
        event_type: str | None = None,
        priority: str | None = None,
    ) -> list[UpdateEvent]:

        statement = select(
            UpdateEvent
        ).order_by(
            UpdateEvent.event_time.desc()
        )
        if event_type:
            statement = statement.where(
            UpdateEvent.event_type
            == event_type.upper()
        )

        if priority:
            statement = statement.where(
            UpdateEvent.priority
            == priority.upper()
        )
        if symbol:
            statement = statement.where(
                UpdateEvent.symbol
                == symbol.upper()
            )

        statement = statement.limit(limit)

        return list(
            self.db.scalars(statement).all()
        )
