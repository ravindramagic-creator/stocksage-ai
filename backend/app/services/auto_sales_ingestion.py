from datetime import date

from sqlalchemy.orm import Session

from app.repositories.auto_sales_repository import AutoSalesRepository
from app.providers.auto_sales_provider import AutoSalesProvider


class AutoSalesIngestion:
    def __init__(self, db: Session, provider: AutoSalesProvider):
        self.repository = AutoSalesRepository(db)
        self.provider = provider

    def ingest_month(self, month: date) -> int:
        records = self.provider.fetch_month(month)

        for record in records:
            self.repository.upsert(record)

        self.repository.db.commit()
        return len(records)
