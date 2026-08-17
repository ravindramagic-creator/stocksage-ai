from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)


class FinancialResultService:

    # Default tolerance for calling a result
    # BEAT / MISS versus MEET.
    #
    # Example:
    #   +2.5%  -> BEAT
    #   +0.5%  -> MEET
    #   -0.5%  -> MEET
    #   -2.5%  -> MISS
    RESULT_TOLERANCE_PCT = Decimal("1.0")

    def __init__(self, db: Session):

        self.repository = (
            FinancialResultRepository(db)
        )

    # =========================================================
    # Growth calculation
    # =========================================================

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

    # =========================================================
    # Surprise calculation
    # =========================================================

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

    # =========================================================
    # Result classification
    # =========================================================

    @classmethod
    def classify_result(
        cls,
        actual: Decimal | None,
        estimate: Decimal | None,
        tolerance: Decimal | None = None,
    ) -> str:

        # No actual result.
        if actual is None:
            return "UNKNOWN"

        # No analyst estimate.
        if estimate is None:
            return "UNKNOWN"

        # Cannot calculate percentage against zero.
        if estimate == 0:
            return "UNKNOWN"

        if tolerance is None:
            tolerance = (
                cls.RESULT_TOLERANCE_PCT
            )

        surprise = cls.calculate_surprise(
            actual,
            estimate,
        )

        if surprise is None:
            return "UNKNOWN"

        if surprise > tolerance:
            return "BEAT"

        if surprise < -tolerance:
            return "MISS"

        return "MEET"

    # =========================================================
    # Compare one metric
    # =========================================================

    @classmethod
    def compare_metric(
        cls,
        actual: Decimal | None,
        estimate: Decimal | None,
        tolerance: Decimal | None = None,
    ) -> tuple[
        Decimal | None,
        str,
    ]:

        surprise = cls.calculate_surprise(
            actual,
            estimate,
        )

        result = cls.classify_result(
            actual,
            estimate,
            tolerance,
        )

        return surprise, result

    # =========================================================
    # Overall result
    # =========================================================

    @staticmethod
    def calculate_overall_result(
        revenue_result: str | None,
        eps_result: str | None,
        pat_result: str | None,
        ebitda_result: str | None,
    ) -> str:

        # Primary metrics.
        primary_results = [
            revenue_result,
            eps_result,
        ]

        primary_results = [
            result
            for result in primary_results
            if result in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        # All available metrics.
        all_results = [
            revenue_result,
            eps_result,
            pat_result,
            ebitda_result,
        ]

        all_results = [
            result
            for result in all_results
            if result in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        # Nothing to compare.
        if not all_results:
            return "UNKNOWN"

        # If both primary metrics are available,
        # use them first.
        if len(primary_results) == 2:

            primary_beats = (
                primary_results.count("BEAT")
            )

            primary_misses = (
                primary_results.count("MISS")
            )

            if primary_beats == 2:
                return "BEAT"

            if primary_misses == 2:
                return "MISS"

        # Fall back to all available metrics.
        beats = all_results.count("BEAT")

        misses = all_results.count("MISS")

        if beats > misses:
            return "BEAT"

        if misses > beats:
            return "MISS"

        return "MEET"

    # =========================================================
    # Create result
    # =========================================================

    def create_result(
        self,
        *,
        symbol: str,
        company_name: str | None,
        period_ended: date | None,
        period_type: str | None,
        consolidated: bool,

        # -----------------------------------------------------
        # Revenue
        # -----------------------------------------------------

        revenue,
        revenue_yoy=None,
        revenue_qoq=None,
        revenue_estimate=None,
        revenue_surprise_pct=None,
        revenue_result=None,

        # -----------------------------------------------------
        # EBITDA
        # -----------------------------------------------------

        ebitda=None,
        ebitda_yoy=None,
        ebitda_qoq=None,
        ebitda_estimate=None,
        ebitda_surprise_pct=None,
        ebitda_result=None,

        # -----------------------------------------------------
        # PAT
        # -----------------------------------------------------

        pat=None,
        pat_yoy=None,
        pat_qoq=None,
        pat_estimate=None,
        pat_surprise_pct=None,
        pat_result=None,

        # -----------------------------------------------------
        # EPS
        # -----------------------------------------------------

        eps=None,
        eps_yoy=None,
        eps_estimate=None,
        eps_surprise_pct=None,
        eps_result=None,

        # -----------------------------------------------------
        # Overall
        # -----------------------------------------------------

        overall_result=None,

        # -----------------------------------------------------
        # Other
        # -----------------------------------------------------

        market_view=None,
        summary=None,
        source=None,
        source_url=None,
        broadcast_date=None,
    ):

        # -----------------------------------------------------
        # Calculate missing Revenue comparison
        # -----------------------------------------------------

        if revenue_estimate is not None:

            if revenue_surprise_pct is None:

                revenue_surprise_pct = (
                    self.calculate_surprise(
                        revenue,
                        revenue_estimate,
                    )
                )

            if revenue_result is None:

                revenue_result = (
                    self.classify_result(
                        revenue,
                        revenue_estimate,
                    )
                )

        # -----------------------------------------------------
        # Calculate missing EBITDA comparison
        # -----------------------------------------------------

        if ebitda_estimate is not None:

            if ebitda_surprise_pct is None:

                ebitda_surprise_pct = (
                    self.calculate_surprise(
                        ebitda,
                        ebitda_estimate,
                    )
                )

            if ebitda_result is None:

                ebitda_result = (
                    self.classify_result(
                        ebitda,
                        ebitda_estimate,
                    )
                )

        # -----------------------------------------------------
        # Calculate missing PAT comparison
        # -----------------------------------------------------

        if pat_estimate is not None:

            if pat_surprise_pct is None:

                pat_surprise_pct = (
                    self.calculate_surprise(
                        pat,
                        pat_estimate,
                    )
                )

            if pat_result is None:

                pat_result = (
                    self.classify_result(
                        pat,
                        pat_estimate,
                    )
                )

        # -----------------------------------------------------
        # Calculate missing EPS comparison
        # -----------------------------------------------------

        if eps_estimate is not None:

            if eps_surprise_pct is None:

                eps_surprise_pct = (
                    self.calculate_surprise(
                        eps,
                        eps_estimate,
                    )
                )

            if eps_result is None:

                eps_result = (
                    self.classify_result(
                        eps,
                        eps_estimate,
                    )
                )

        # -----------------------------------------------------
        # Calculate overall result
        # -----------------------------------------------------

        if overall_result is None:

            overall_result = (
                self.calculate_overall_result(
                    revenue_result,
                    eps_result,
                    pat_result,
                    ebitda_result,
                )
            )

        # -----------------------------------------------------
        # Store
        # -----------------------------------------------------

        return self.repository.create(

            symbol=symbol,

            company_name=company_name,

            period_ended=period_ended,

            period_type=period_type,

            consolidated=consolidated,

            # Revenue
            revenue=revenue,

            revenue_yoy=revenue_yoy,

            revenue_qoq=revenue_qoq,

            revenue_estimate=revenue_estimate,

            revenue_surprise_pct=(
                revenue_surprise_pct
            ),

            revenue_result=revenue_result,

            # EBITDA
            ebitda=ebitda,

            ebitda_yoy=ebitda_yoy,

            ebitda_qoq=ebitda_qoq,

            ebitda_estimate=ebitda_estimate,

            ebitda_surprise_pct=(
                ebitda_surprise_pct
            ),

            ebitda_result=ebitda_result,

            # PAT
            pat=pat,

            pat_yoy=pat_yoy,

            pat_qoq=pat_qoq,

            pat_estimate=pat_estimate,

            pat_surprise_pct=(
                pat_surprise_pct
            ),

            pat_result=pat_result,

            # EPS
            eps=eps,

            eps_yoy=eps_yoy,

            eps_estimate=eps_estimate,

            eps_surprise_pct=(
                eps_surprise_pct
            ),

            eps_result=eps_result,

            # Overall
            overall_result=overall_result,

            # Other
            market_view=market_view,

            summary=summary,

            source=source,

            source_url=source_url,

            broadcast_date=broadcast_date,
        )

    # =========================================================
    # Get latest
    # =========================================================

    def get_latest(
        self,
        symbol: str,
    ):

        return self.repository.get_latest(
            symbol
        )

    # =========================================================
    # Get recent
    # =========================================================

    def get_recent(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ):

        return self.repository.get_recent(
            symbol=symbol,
            limit=limit,
        )
