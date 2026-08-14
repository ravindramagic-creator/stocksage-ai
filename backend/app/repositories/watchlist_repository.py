from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.watchlist import Watchlist


class WatchlistRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Watchlist]:
        statement = select(Watchlist)

        return list(self.db.scalars(statement).all())

    def get_by_symbol(self, symbol: str) -> Watchlist | None:
        statement = (
            select(Watchlist)
            .join(Watchlist.stock)
            .where(Stock.symbol == symbol.upper())
        )

        return self.db.scalars(statement).first()

    def add(self, stock: Stock) -> Watchlist:
        item = Watchlist(stock_id=stock.id)

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def delete(self, item: Watchlist) -> None:
        self.db.delete(item)
        self.db.commit()

