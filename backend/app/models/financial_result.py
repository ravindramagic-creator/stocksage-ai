from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FinancialResult(Base):

    __tablename__ = "financial_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    company_name: Mapped[str | None] = (
        mapped_column(
            String(200),
            nullable=True,
        )
    )

    period_ended: Mapped[datetime | None] = (
        mapped_column(
            Date,
            nullable=True,
            index=True,
        )
    )

    period_type: Mapped[str | None] = (
        mapped_column(
            String(30),
            nullable=True,
        )
    )

    consolidated: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )

    revenue: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    revenue_yoy: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    revenue_qoq: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    ebitda: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    ebitda_yoy: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    ebitda_qoq: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    pat: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    pat_yoy: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    pat_qoq: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    eps: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(12, 4),
            nullable=True,
        )
    )

    eps_yoy: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    market_view: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    summary: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    source: Mapped[str | None] = (
        mapped_column(
            String(100),
            nullable=True,
        )
    )

    source_url: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    broadcast_date: Mapped[datetime | None] = (
        mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
