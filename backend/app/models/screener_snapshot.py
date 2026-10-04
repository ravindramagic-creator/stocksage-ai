from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ScreenerSnapshot(Base):
    __tablename__ = "screener_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)

    score: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(40), nullable=False)
    data_completeness: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    price: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    pe: Mapped[float | None] = mapped_column(Float)
    peg: Mapped[float | None] = mapped_column(Float)
    pb: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    roce: Mapped[float | None] = mapped_column(Float)
    debt_to_equity: Mapped[float | None] = mapped_column(Float)

    revenue_growth: Mapped[float | None] = mapped_column(Float)
    profit_growth: Mapped[float | None] = mapped_column(Float)
    eps_growth: Mapped[float | None] = mapped_column(Float)

    sma50: Mapped[float | None] = mapped_column(Float)
    sma200: Mapped[float | None] = mapped_column(Float)
    rsi14: Mapped[float | None] = mapped_column(Float)
    momentum_6m: Mapped[float | None] = mapped_column(Float)

    target_upside: Mapped[float | None] = mapped_column(Float)
    analyst_beat_rate: Mapped[float | None] = mapped_column(Float)

    fundamental_score: Mapped[float | None] = mapped_column(Float)
    valuation_score: Mapped[float | None] = mapped_column(Float)
    technical_score: Mapped[float | None] = mapped_column(Float)
    analyst_score: Mapped[float | None] = mapped_column(Float)

    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    snapshot_version: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
