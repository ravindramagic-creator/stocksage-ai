from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)


class FinancialResultService:

    def __init__(self, db: Session):

        self.repository = (
            FinancialResultRepository(db)
        )

    @staticmethod
    def calculate_growth(
        current: Decimal | None,
        previous: Decimal | None,
    ) -> Decimal | None:

        if current is None:
            return None

        if previous is None:
            return None

        if previous == 0:
            return None

        return (
            (current - previous)
            / abs(previous)
        ) * Decimal("100")

    @staticmethod
    def classify_result(
        actual: Decimal | None,
        estimate: Decimal | None,
    ) -> str | None:

        if actual is None:
            return None

        if estimate is None:
            return "UNKNOWN"

        if estimate == 0:
            return "UNKNOWN"

        difference = (
            (actual - estimate)
            / abs(estimate)
        ) * Decimal("100")

        if difference >= Decimal("5"):
            return "BEAT"

        if difference <= Decimal("-5"):
            return "MISS"

        return "MEET"

    def create_result(
        self,
        *,
        symbol: str,
        company_name: str | None,
        period_ended: date | None,
        period_type: str | None,
        consolidated: bool,
        revenue,
        revenue_yoy=None,
        revenue_qoq=None,
        ebitda=None,
        ebitda_yoy=None,
        ebitda_qoq=None,
        pat=None,
        pat_yoy=None,
        pat_qoq=None,
        eps=None,
        eps_yoy=None,
        market_view=None,
        summary=None,
        source=None,
        source_url=None,
        broadcast_date=None,
    ):

        return self.repository.create(
            symbol=symbol,
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

    def get_latest(
        self,
        symbol: str,
    ):

        return self.repository.get_latest(
            symbol
        )

    def get_recent(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ):

        return self.repository.get_recent(
            symbol=symbol,
            limit=limit,
        )
