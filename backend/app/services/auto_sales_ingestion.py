from datetime import date

from sqlalchemy.orm import Session

from app.providers.auto_sales_provider import AutoSalesProvider
from app.repositories.auto_sales_repository import AutoSalesRepository


class AutoSalesIngestion:
    def __init__(self, db: Session, provider: AutoSalesProvider):
        self.repository = AutoSalesRepository(db)
        self.provider = provider

    @staticmethod
    def _month_start(value: date) -> date:
        return value.replace(day=1)

    def _normalize(self, record: dict) -> dict:
        normalized = dict(record)
        normalized["symbol"] = str(normalized["symbol"]).upper().strip()
        normalized["segment"] = str(normalized["segment"]).upper().strip()
        normalized["month"] = self._month_start(normalized["month"])

        # Registrations are the source metric for the current provider.
        if normalized.get("total_sales") is None:
            normalized["total_sales"] = normalized.get("registrations")

        return normalized

    def ingest_month(self, month: date) -> int:
        records = self.provider.fetch_month(self._month_start(month))
        count = 0

        for record in records:
            self.repository.upsert(self._normalize(record))
            count += 1

        self.repository.db.commit()
        return count

    def ingest_history(self, segment: str | None = None) -> int:
        records = self.provider.fetch_history(segment=segment)
        count = 0

        for record in records:
            self.repository.upsert(self._normalize(record))
            count += 1

        self.repository.db.commit()
        return count
