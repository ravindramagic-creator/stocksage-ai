from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AutoSales(Base):
    __tablename__ = "auto_sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    registrations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    domestic_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    export_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)

    yoy_growth: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    mom_growth: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    market_share: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    data_type: Mapped[str] = mapped_column(String(30), nullable=False, default="REGISTRATION")
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="VAHAN")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_projected: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("symbol", "segment", "month", "data_type", name="uq_auto_sales_period"),
    )
