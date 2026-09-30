from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auto_sales import AutoSales


class AutoSalesRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        symbol: str | None = None,
        segment: str | None = None,
        start_month: date | None = None,
        end_month: date | None = None,
        data_type: str | None = None,
    ) -> list[AutoSales]:
        query = select(AutoSales)

        if symbol:
            query = query.where(AutoSales.symbol == symbol.upper())
        if segment:
            query = query.where(AutoSales.segment == segment.upper())
        if start_month:
            query = query.where(AutoSales.month >= start_month)
        if end_month:
            query = query.where(AutoSales.month <= end_month)
        if data_type:
            query = query.where(AutoSales.data_type == data_type.upper())

        query = query.order_by(AutoSales.month.asc(), AutoSales.company_name.asc())
        return list(self.db.scalars(query).all())

    def upsert(self, values: dict) -> AutoSales:
        stmt = select(AutoSales).where(
            AutoSales.symbol == values["symbol"],
            AutoSales.segment == values["segment"],
            AutoSales.month == values["month"],
            AutoSales.data_type == values.get("data_type", "REGISTRATION"),
        )
        obj = self.db.scalar(stmt)

        if obj is None:
            obj = AutoSales(**values)
            self.db.add(obj)
        else:
            for key, value in values.items():
                setattr(obj, key, value)

        self.db.flush()
        return obj
