from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UpdateEvent(Base):
    __tablename__ = "update_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    old_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    new_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    event_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
