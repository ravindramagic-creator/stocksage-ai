from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.stock import Stock


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    stock: Mapped[Stock] = relationship()
