from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import (
    FinancialResult,
)


class FinancialResultRepository:

    def __init__(self, db: Session):

        self.db = db

    def create(
        self,
        *,
        symbol: str,
        company_name: str | None,
        period_ended: date | None,
        period_type: str | None,
        consolidated: bool,
        revenue,
        revenue_yoy,
        revenue_qoq,
        ebitda,
        ebitda_yoy,
        ebitda_qoq,
        pat,
        pat_yoy,
        pat_qoq,
        eps,
        eps_yoy,
        market_view: str | None,
        summary: str | None,
        source: str | None,
        source_url: str | None,
        broadcast_date,
    ):

        result = FinancialResult(
            symbol=symbol.upper(),
            company_name=company_name,
            period_ended=period_ended,
            period_type=period_type,
            consolidated=consolidated,
            revenue=revenue,
            revenue_yoy=revenue_yoy,
            revenue_qoq=revenue_qoq,
            ebitda=ebitda,
            ebitda_yoy=ebitda_yoy,
            ebitda_qoq=ebitda_qoq,
            pat=pat,
            pat_yoy=pat_yoy,
            pat_qoq=pat_qoq,
            eps=eps,
            eps_yoy=eps_yoy,
            market_view=market_view,
            summary=summary,
            source=source,
            source_url=source_url,
            broadcast_date=broadcast_date,
        )

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)

        return result

    def get_latest(
        self,
        symbol: str,
    ):

        statement = (
            select(FinancialResult)
            .where(
                FinancialResult.symbol
                == symbol.upper()
            )
            .order_by(
                FinancialResult.period_ended.desc()
            )
            .limit(1)
        )

        return self.db.scalars(
            statement
        ).first()

    def get_recent(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ):

        statement = select(
            FinancialResult
        ).order_by(
            FinancialResult.period_ended.desc()
        )

        if symbol:

            statement = statement.where(
                FinancialResult.symbol
                == symbol.upper()
            )

        statement = statement.limit(
            min(max(limit, 1), 100)
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )
