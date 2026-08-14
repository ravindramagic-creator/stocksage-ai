from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.repositories.stock_repository import (
    StockRepository,
)


class StockService:

    def __init__(self, db: Session):
        self.repository = StockRepository(db)

    def get_all(self) -> list[Stock]:
        return self.repository.get_all()

    def get_by_symbol(
        self,
        symbol: str,
    ) -> Stock | None:

        return self.repository.get_by_symbol(
            symbol.strip().upper()
        )

    def search(
        self,
        query: str,
    ) -> list[Stock]:

        return self.repository.search(
            query.strip()
        )
