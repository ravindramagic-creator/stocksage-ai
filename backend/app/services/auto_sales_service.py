from datetime import date

from sqlalchemy.orm import Session

from app.repositories.auto_sales_repository import AutoSalesRepository


class AutoSalesService:
    def __init__(self, db: Session):
        self.repository = AutoSalesRepository(db)

    def get_sales(
        self,
        symbol: str | None = None,
        segment: str | None = None,
        start_month: date | None = None,
        end_month: date | None = None,
        data_type: str | None = None,
    ):
        return self.repository.list(
            symbol=symbol,
            segment=segment,
            start_month=start_month,
            end_month=end_month,
            data_type=data_type,
        )

    def upsert_many(self, records: list[dict]) -> int:
        for record in records:
            self.repository.upsert(record)
        self.repository.db.commit()
        return len(records)
