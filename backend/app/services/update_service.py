from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.update_event_repository import (
    UpdateEventRepository,
)

from app.services.events.event_priority import (
    get_priority,
)


class UpdateService:

    def __init__(self, db: Session):
        self.repository = UpdateEventRepository(db)

    def create_event(
        self,
        *,
        symbol: str,
        event_type: str,
        title: str,
        description: str | None = None,
        source: str | None = None,
        source_url: str | None = None,
        old_value: float | None = None,
        new_value: float | None = None,
        event_key: str,
        event_time: datetime | None = None,
    ):
        # Don't create the same event twice.
        if self.repository.exists(event_key):
            return None

        # Use current UTC time when the provider
        # doesn't supply an event time.
        if event_time is None:
            event_time = datetime.now(
                timezone.utc
            )

        # Determine event priority.
        priority = get_priority(
            event_type
        )

        return self.repository.create(
            symbol=symbol,
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

    def get_recent(
        self,
        limit: int = 50,
        symbol: str | None = None,
        event_type: str | None = None,
        priority: str | None = None,
    ):
        limit = min(
            max(limit, 1),
            200,
        )

        return self.repository.get_recent(
            limit=limit,
            symbol=symbol,
            event_type=event_type,
            priority=priority,
        )
