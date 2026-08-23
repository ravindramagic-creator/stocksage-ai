from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)


class FinancialResultService:

    RESULT_TOLERANCE_PCT = Decimal("1.0")

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
    def calculate_surprise(
        actual: Decimal | None,
        estimate: Decimal | None,
    ) -> Decimal | None:

        if actual is None:
            return None

        if estimate is None:
            return None

        if estimate == 0:
            return None

        return (
            (actual - estimate)
            / abs(estimate)
        ) * Decimal("100")

    @classmethod
    def classify_result(
        cls,
        actual: Decimal | None,
        estimate: Decimal | None,
    ) -> str:

        surprise = cls.calculate_surprise(
            actual,
            estimate,
        )

        if surprise is None:
            return "UNKNOWN"

        if surprise > cls.RESULT_TOLERANCE_PCT:
            return "BEAT"

        if surprise < -cls.RESULT_TOLERANCE_PCT:
            return "MISS"

        return "MEET"

    @staticmethod
    def calculate_overall_result(
        revenue_result,
        eps_result,
        pat_result,
        ebitda_result,
    ) -> str:

        results = [
            revenue_result,
            eps_result,
            pat_result,
            ebitda_result,
        ]

        results = [
            value
            for value in results
            if value in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        if not results:
            return "UNKNOWN"

        beats = results.count("BEAT")
        misses = results.count("MISS")

        if beats > misses:
            return "BEAT"

        if misses > beats:
            return "MISS"

        return "MEET"

    # =========================================================
    # Prepare comparison values
    # =========================================================

    def prepare_comparison(
        self,
        actual,
        estimate,
    ):

        surprise = self.calculate_surprise(
            actual,
            estimate,
        )

        result = self.classify_result(
            actual,
            estimate,
        )

        return surprise, result

    # =========================================================
    # Save/update result
    # =========================================================

    def save_result(
        self,
        *,
        symbol,
        company_name,
        period_ended,
        period_type,
        consolidated,

        revenue,
        revenue_yoy=None,
        revenue_qoq=None,
        revenue_estimate=None,

        ebitda=None,
        ebitda_yoy=None,
        ebitda_qoq=None,
        ebitda_estimate=None,

        pat=None,
        pat_yoy=None,
        pat_qoq=None,
        pat_estimate=None,

        eps=None,
        eps_yoy=None,
        eps_estimate=None,

        market_view=None,
        summary=None,
        source=None,
        source_url=None,
        broadcast_date=None,
    ):

        revenue_surprise, revenue_result = (
            self.prepare_comparison(
                revenue,
                revenue_estimate,
            )
        )

        ebitda_surprise, ebitda_result = (
            self.prepare_comparison(
                ebitda,
                ebitda_estimate,
            )
        )

        pat_surprise, pat_result = (
            self.prepare_comparison(
                pat,
                pat_estimate,
            )
        )

        eps_surprise, eps_result = (
            self.prepare_comparison(
                eps,
                eps_estimate,
            )
        )

        overall_result = (
            self.calculate_overall_result(
                revenue_result,
                eps_result,
                pat_result,
                ebitda_result,
            )
        )

        values = {
            "symbol": symbol.upper(),
            "company_name": company_name,

            "period_ended": period_ended,
            "period_type": period_type,
            "consolidated": consolidated,

            "revenue": revenue,
            "revenue_yoy": revenue_yoy,
            "revenue_qoq": revenue_qoq,
            "revenue_estimate": revenue_estimate,
            "revenue_surprise_pct": revenue_surprise,
            "revenue_result": revenue_result,

            "ebitda": ebitda,
            "ebitda_yoy": ebitda_yoy,
            "ebitda_qoq": ebitda_qoq,
            "ebitda_estimate": ebitda_estimate,
            "ebitda_surprise_pct": ebitda_surprise,
            "ebitda_result": ebitda_result,

            "pat": pat,
            "pat_yoy": pat_yoy,
            "pat_qoq": pat_qoq,
            "pat_estimate": pat_estimate,
            "pat_surprise_pct": pat_surprise,
            "pat_result": pat_result,

            "eps": eps,
            "eps_yoy": eps_yoy,
            "eps_estimate": eps_estimate,
            "eps_surprise_pct": eps_surprise,
            "eps_result": eps_result,

            "overall_result": overall_result,

            "market_view": market_view,
            "summary": summary,

            "source": source,
            "source_url": source_url,
            "broadcast_date": broadcast_date,
        }

        existing = self.repository.get_by_period(
            symbol,
            period_ended,
        )

        if existing:

            return self.repository.update(
                existing,
                **values,
            )

        return self.repository.create(
            **values,
        )

    # =========================================================
    # Queries
    # =========================================================

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
