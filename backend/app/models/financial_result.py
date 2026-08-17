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

    # ---------------------------------------------------------
    # Period information
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Revenue
    # ---------------------------------------------------------

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

    # Analyst consensus estimate
    revenue_estimate: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    # Actual vs estimate percentage
    revenue_surprise_pct: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    # BEAT / MISS / MEET / UNKNOWN
    revenue_result: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # EBITDA
    # ---------------------------------------------------------

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

    # Analyst consensus estimate
    ebitda_estimate: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    # Actual vs estimate percentage
    ebitda_surprise_pct: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    # BEAT / MISS / MEET / UNKNOWN
    ebitda_result: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # PAT / Net Profit
    # ---------------------------------------------------------

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

    # Analyst consensus estimate
    pat_estimate: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(20, 2),
            nullable=True,
        )
    )

    # Actual vs estimate percentage
    pat_surprise_pct: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    # BEAT / MISS / MEET / UNKNOWN
    pat_result: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # EPS
    # ---------------------------------------------------------

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

    # Analyst consensus estimate
    eps_estimate: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(12, 4),
            nullable=True,
        )
    )

    # Actual vs estimate percentage
    eps_surprise_pct: Mapped[Decimal | None] = (
        mapped_column(
            Numeric(10, 2),
            nullable=True,
        )
    )

    # BEAT / MISS / MEET / UNKNOWN
    eps_result: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # Overall result
    # ---------------------------------------------------------

    # BEAT / MISS / MEET / UNKNOWN
    #
    # This is calculated by StockSage based on the
    # available financial metrics and their estimates.
    overall_result: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # Market view
    # ---------------------------------------------------------

    market_view: Mapped[str | None] = (
        mapped_column(
            String(20),
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary: Mapped[str | None] = (
        mapped_column(
            Text,
            nullable=True,
        )
    )

    # ---------------------------------------------------------
    # Source
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
