from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    exchange: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="NSE",
    )
    sector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
