from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (UniqueConstraint("symbol", name="uq_market_snapshot_symbol"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    price: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    pe: Mapped[float | None] = mapped_column(Float)
    pb: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    roce: Mapped[float | None] = mapped_column(Float)
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    revenue_growth: Mapped[float | None] = mapped_column(Float)
    profit_growth: Mapped[float | None] = mapped_column(Float)
    target_upside: Mapped[float | None] = mapped_column(Float)
    sma50: Mapped[float | None] = mapped_column(Float)
    sma200: Mapped[float | None] = mapped_column(Float)
    rsi14: Mapped[float | None] = mapped_column(Float)
    rsi_weekly: Mapped[float | None] = mapped_column(Float)
    rsi_monthly: Mapped[float | None] = mapped_column(Float)
    momentum_3m: Mapped[float | None] = mapped_column(Float)
    momentum_6m: Mapped[float | None] = mapped_column(Float)
    analyst_beat_rate: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="ok", nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
