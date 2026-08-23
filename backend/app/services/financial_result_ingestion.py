from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)

from app.services.nse_financial_result_provider import (
    NSEFinancialResultProvider,
)

from app.services.analyst_estimate_provider import (
    AnalystEstimateProvider,
)


class FinancialResultIngestion:

    # ---------------------------------------------------------
    # UI may request 8 quarters.
    #
    # We fetch more because YoY needs the same quarter
    # from the previous year.
    # ---------------------------------------------------------

    PROVIDER_HISTORY_LIMIT = 20

    # ---------------------------------------------------------
    # Beat / miss tolerance.
    #
    # +1% or -1% is considered MEET.
    # ---------------------------------------------------------

    RESULT_TOLERANCE_PCT = Decimal(
        "1.0"
    )

    def __init__(
        self,
        db: Session,
    ):

        self.db = db

        self.repository = (
            FinancialResultRepository(db)
        )

        self.nse_provider = (
            NSEFinancialResultProvider()
        )

        self.estimate_provider = (
            AnalystEstimateProvider()
        )

    # =========================================================
    # Growth
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
            (
                current - previous
            )
            / abs(previous)
        ) * Decimal("100")

    # =========================================================
    # Surprise
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
            (
                actual - estimate
            )
            / abs(estimate)
        ) * Decimal("100")

    # =========================================================
    # Beat / Miss / Meet
    # =========================================================

    @classmethod
    def classify_result(
        cls,
        actual: Decimal | None,
        estimate: Decimal | None,
    ) -> str:

        if actual is None:
            return "UNKNOWN"

        if estimate is None:
            return "UNKNOWN"

        surprise = (
            cls.calculate_surprise(
                actual,
                estimate,
            )
        )

        if surprise is None:
            return "UNKNOWN"

        if (
            surprise
            > cls.RESULT_TOLERANCE_PCT
        ):
            return "BEAT"

        if (
            surprise
            < -cls.RESULT_TOLERANCE_PCT
        ):
            return "MISS"

        return "MEET"

    # =========================================================
    # Previous year
    # =========================================================

    @staticmethod
    def find_previous_year(
        current_period: date,
        values: dict[
            date,
            dict[str, Decimal | None],
        ],
    ) -> dict[str, Decimal | None] | None:

        target_year = (
            current_period.year - 1
        )

        # First try exact month match.

        for candidate_period in values:

            if (
                candidate_period.year
                == target_year
                and candidate_period.month
                == current_period.month
            ):

                return values[
                    candidate_period
                ]

        # Fallback for filing date differences.

        candidates = []

        for candidate_period in values:

            days_difference = (
                current_period
                - candidate_period
            ).days

            if (
                330
                <= days_difference
                <= 400
            ):

                candidates.append(
                    (
                        abs(
                            days_difference
                            - 365
                        ),
                        candidate_period,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x[0]
        )

        return values[
            candidates[0][1]
        ]

    # =========================================================
    # Previous quarter
    # =========================================================

    @staticmethod
    def find_previous_quarter(
        current_period: date,
        values: dict[
            date,
            dict[str, Decimal | None],
        ],
    ) -> dict[str, Decimal | None] | None:

        candidates = []

        for candidate_period in values:

            days_difference = (
                current_period
                - candidate_period
            ).days

            if (
                70
                <= days_difference
                <= 110
            ):

                candidates.append(
                    (
                        days_difference,
                        candidate_period,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x[0]
        )

        return values[
            candidates[0][1]
        ]

    # =========================================================
    # Overall result
    # =========================================================

    @staticmethod
    def calculate_overall_result(
        revenue_result: str,
        eps_result: str,
        pat_result: str,
        ebitda_result: str,
    ) -> str:

        primary = [
            revenue_result,
            eps_result,
        ]

        primary = [
            value
            for value in primary
            if value
            in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        all_results = [
            revenue_result,
            eps_result,
            pat_result,
            ebitda_result,
        ]

        all_results = [
            value
            for value in all_results
            if value
            in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        if not all_results:
            return "UNKNOWN"

        # Revenue + EPS are the primary
        # market-facing metrics.

        if len(primary) == 2:

            beats = primary.count(
                "BEAT"
            )

            misses = primary.count(
                "MISS"
            )

            if beats == 2:
                return "BEAT"

            if misses == 2:
                return "MISS"

        beats = all_results.count(
            "BEAT"
        )

        misses = all_results.count(
            "MISS"
        )

        if beats > misses:
            return "BEAT"

        if misses > beats:
            return "MISS"

        return "MEET"

    # =========================================================
    # Summary
    # =========================================================

    @staticmethod
    def build_summary(
        revenue_yoy: Decimal | None,
        pat_yoy: Decimal | None,
        eps_yoy: Decimal | None,
        overall_result: str,
    ) -> str:

        parts = []

        if revenue_yoy is not None:

            parts.append(
                f"Revenue "
                f"{revenue_yoy:+.1f}% YoY"
            )

        if pat_yoy is not None:

            parts.append(
                f"PAT "
                f"{pat_yoy:+.1f}% YoY"
            )

        if eps_yoy is not None:

            parts.append(
                f"EPS "
                f"{eps_yoy:+.1f}% YoY"
            )

        summary = (
            ", ".join(parts)
            if parts
            else
            "Quarterly financial results."
        )

        if overall_result != "UNKNOWN":

            summary += (
                f" Result: {overall_result}."
            )

        else:

            summary += "."

        return summary

    # =========================================================
    # Update existing database row
    # =========================================================

    def update_existing(
        self,
        existing,
        *,
        revenue,
        revenue_yoy,
        revenue_qoq,
        revenue_estimate,
        revenue_surprise_pct,
        revenue_result,

        ebitda,
        ebitda_yoy,
        ebitda_qoq,
        ebitda_estimate,
        ebitda_surprise_pct,
        ebitda_result,

        pat,
        pat_yoy,
        pat_qoq,
        pat_estimate,
        pat_surprise_pct,
        pat_result,

        eps,
        eps_yoy,
        eps_estimate,
        eps_surprise_pct,
        eps_result,

        overall_result,
        summary,
    ):

        # -----------------------------------------------------
        # Actual values
        # -----------------------------------------------------

        if revenue is not None:
            existing.revenue = revenue

        if ebitda is not None:
            existing.ebitda = ebitda

        if pat is not None:
            existing.pat = pat

        if eps is not None:
            existing.eps = eps

        # -----------------------------------------------------
        # Growth
        # -----------------------------------------------------

        if revenue_yoy is not None:
            existing.revenue_yoy = (
                revenue_yoy
            )

        if revenue_qoq is not None:
            existing.revenue_qoq = (
                revenue_qoq
            )

        if ebitda_yoy is not None:
            existing.ebitda_yoy = (
                ebitda_yoy
            )

        if ebitda_qoq is not None:
            existing.ebitda_qoq = (
                ebitda_qoq
            )

        if pat_yoy is not None:
            existing.pat_yoy = pat_yoy

        if pat_qoq is not None:
            existing.pat_qoq = pat_qoq

        if eps_yoy is not None:
            existing.eps_yoy = eps_yoy

        # -----------------------------------------------------
        # Estimates
        # -----------------------------------------------------

        if revenue_estimate is not None:

            existing.revenue_estimate = (
                revenue_estimate
            )

        if ebitda_estimate is not None:

            existing.ebitda_estimate = (
                ebitda_estimate
            )

        if pat_estimate is not None:

            existing.pat_estimate = (
                pat_estimate
            )

        if eps_estimate is not None:

            existing.eps_estimate = (
                eps_estimate
            )

        # -----------------------------------------------------
        # Surprise
        # -----------------------------------------------------

        if revenue_surprise_pct is not None:

            existing.revenue_surprise_pct = (
                revenue_surprise_pct
            )

        if ebitda_surprise_pct is not None:

            existing.ebitda_surprise_pct = (
                ebitda_surprise_pct
            )

        if pat_surprise_pct is not None:

            existing.pat_surprise_pct = (
                pat_surprise_pct
            )

        if eps_surprise_pct is not None:

            existing.eps_surprise_pct = (
                eps_surprise_pct
            )

        # -----------------------------------------------------
        # Classification
        # -----------------------------------------------------

        existing.revenue_result = (
            revenue_result
        )

        existing.ebitda_result = (
            ebitda_result
        )

        existing.pat_result = (
            pat_result
        )

        existing.eps_result = (
            eps_result
        )

        existing.overall_result = (
            overall_result
        )

        if summary:
            existing.summary = summary

        return existing

    # =========================================================
    # Ingest
    # =========================================================

    def ingest(
        self,
        symbol: str,
        limit: int = 8,
    ) -> list:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        # -----------------------------------------------------
        # Fetch MORE than UI limit.
        #
        # Example:
        #
        # UI = 8
        #
        # Fetch = 20
        #
        # This allows Jun-2025 to find Jun-2024.
        # -----------------------------------------------------

        fetch_limit = max(
            self.PROVIDER_HISTORY_LIMIT,
            limit + 8,
        )

        print(
            f"Fetching up to "
            f"{fetch_limit} quarters for "
            f"{symbol}"
        )

        provider_results = (
            self.nse_provider.get_results(
                symbol,
                limit=fetch_limit,
            )
        )

        if not provider_results:

            raise RuntimeError(
                f"NSE returned no financial "
                f"results for {symbol}"
            )

        # =====================================================
        # Analyst estimates
        # =====================================================

        try:

            estimates = (
                self.estimate_provider
                .get_normalized_estimates(
                    symbol
                )
            )

        except Exception as exc:

            print(
                f"Estimate provider failed "
                f"for {symbol}: {exc}"
            )

            estimates = {}

        print(
            f"Loaded "
            f"{len(estimates)} "
            f"estimate periods for "
            f"{symbol}"
        )

        # =====================================================
        # Normalize actuals
        # =====================================================

        values: dict[
            date,
            dict[str, Decimal | None],
        ] = {}

        for item in provider_results:

            period = item.get(
                "period_ended"
            )

            if period is None:
                continue

            current = {
                "revenue": item.get(
                    "revenue"
                ),
                "ebitda": item.get(
                    "ebitda"
                ),
                "pat": item.get(
                    "pat"
                ),
                "eps": item.get(
                    "eps"
                ),
            }

            if period not in values:

                values[period] = current

                continue

            # Prefer non-null values.

            existing = values[
                period
            ]

            for field in (
                "revenue",
                "ebitda",
                "pat",
                "eps",
            ):

                if (
                    existing.get(field)
                    is None
                    and current.get(field)
                    is not None
                ):

                    existing[field] = (
                        current[field]
                    )

        periods = sorted(
            values.keys(),
            reverse=True,
        )

        if not periods:

            raise RuntimeError(
                f"No valid financial "
                f"periods for {symbol}"
            )

        processed = []

        # =====================================================
        # Process each period
        # =====================================================

        for period in periods:

            current = values[
                period
            ]

            previous_year = (
                self.find_previous_year(
                    period,
                    values,
                )
            )

            previous_quarter = (
                self.find_previous_quarter(
                    period,
                    values,
                )
            )

            # -------------------------------------------------
            # Growth
            # -------------------------------------------------

            revenue_yoy = (
                self.calculate_growth(
                    current["revenue"],
                    (
                        previous_year[
                            "revenue"
                        ]
                        if previous_year
                        else None
                    ),
                )
            )

            revenue_qoq = (
                self.calculate_growth(
                    current["revenue"],
                    (
                        previous_quarter[
                            "revenue"
                        ]
                        if previous_quarter
                        else None
                    ),
                )
            )

            ebitda_yoy = (
                self.calculate_growth(
                    current["ebitda"],
                    (
                        previous_year[
                            "ebitda"
                        ]
                        if previous_year
                        else None
                    ),
                )
            )

            ebitda_qoq = (
                self.calculate_growth(
                    current["ebitda"],
                    (
                        previous_quarter[
                            "ebitda"
                        ]
                        if previous_quarter
                        else None
                    ),
                )
            )

            pat_yoy = (
                self.calculate_growth(
                    current["pat"],
                    (
                        previous_year[
                            "pat"
                        ]
                        if previous_year
                        else None
                    ),
                )
            )

            pat_qoq = (
                self.calculate_growth(
                    current["pat"],
                    (
                        previous_quarter[
                            "pat"
                        ]
                        if previous_quarter
                        else None
                    ),
                )
            )

            eps_yoy = (
                self.calculate_growth(
                    current["eps"],
                    (
                        previous_year[
                            "eps"
                        ]
                        if previous_year
                        else None
                    ),
                )
            )

            # -------------------------------------------------
            # Estimate
            #
            # Exact period first.
            # -------------------------------------------------

            estimate = (
                estimates.get(
                    period,
                    {},
                )
            )

            revenue_estimate = (
                estimate.get(
                    "revenue_estimate"
                )
            )

            eps_estimate = (
                estimate.get(
                    "eps_estimate"
                )
            )

            # -------------------------------------------------
            # Surprise
            # -------------------------------------------------

            revenue_surprise_pct = (
                self.calculate_surprise(
                    current["revenue"],
                    revenue_estimate,
                )
            )

            eps_surprise_pct = (
                self.calculate_surprise(
                    current["eps"],
                    eps_estimate,
                )
            )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            revenue_result = (
                self.classify_result(
                    current["revenue"],
                    revenue_estimate,
                )
            )

            eps_result = (
                self.classify_result(
                    current["eps"],
                    eps_estimate,
                )
            )

            # -------------------------------------------------
            # EBITDA / PAT estimates
            #
            # We don't invent estimates.
            # -------------------------------------------------

            ebitda_estimate = None
            pat_estimate = None

            ebitda_surprise_pct = None
            pat_surprise_pct = None

            ebitda_result = "UNKNOWN"
            pat_result = "UNKNOWN"

            # -------------------------------------------------
            # Overall
            # -------------------------------------------------

            overall_result = (
                self.calculate_overall_result(
                    revenue_result,
                    eps_result,
                    pat_result,
                    ebitda_result,
                )
            )

            # -------------------------------------------------
            # Summary
            # -------------------------------------------------

            summary = (
                self.build_summary(
                    revenue_yoy,
                    pat_yoy,
                    eps_yoy,
                    overall_result,
                )
            )

            # =================================================
            # Existing DB row
            # =================================================

            existing = (
                self.repository.get_by_period(
                    symbol,
                    period,
                )
            )

            if existing:

                self.update_existing(
                    existing,

                    revenue=current[
                        "revenue"
                    ],

                    revenue_yoy=revenue_yoy,

                    revenue_qoq=revenue_qoq,

                    revenue_estimate=(
                        revenue_estimate
                    ),

                    revenue_surprise_pct=(
                        revenue_surprise_pct
                    ),

                    revenue_result=(
                        revenue_result
                    ),

                    ebitda=current[
                        "ebitda"
                    ],

                    ebitda_yoy=ebitda_yoy,

                    ebitda_qoq=ebitda_qoq,

                    ebitda_estimate=(
                        ebitda_estimate
                    ),

                    ebitda_surprise_pct=(
                        ebitda_surprise_pct
                    ),

                    ebitda_result=(
                        ebitda_result
                    ),

                    pat=current["pat"],

                    pat_yoy=pat_yoy,

                    pat_qoq=pat_qoq,

                    pat_estimate=(
                        pat_estimate
                    ),

                    pat_surprise_pct=(
                        pat_surprise_pct
                    ),

                    pat_result=(
                        pat_result
                    ),

                    eps=current["eps"],

                    eps_yoy=eps_yoy,

                    eps_estimate=(
                        eps_estimate
                    ),

                    eps_surprise_pct=(
                        eps_surprise_pct
                    ),

                    eps_result=(
                        eps_result
                    ),

                    overall_result=(
                        overall_result
                    ),

                    summary=summary,
                )

                processed.append(
                    existing
                )

                print(
                    f"Updated "
                    f"{symbol} "
                    f"{period} "
                    f"overall={overall_result}"
                )

                continue

            # =================================================
            # New record
            # =================================================

            result = (
                self.repository.create(
                    symbol=symbol,

                    company_name=symbol,

                    period_ended=period,

                    period_type="Quarterly",

                    consolidated=True,

                    revenue=current[
                        "revenue"
                    ],

                    revenue_yoy=revenue_yoy,

                    revenue_qoq=revenue_qoq,

                    revenue_estimate=(
                        revenue_estimate
                    ),

                    revenue_surprise_pct=(
                        revenue_surprise_pct
                    ),

                    revenue_result=(
                        revenue_result
                    ),

                    ebitda=current[
                        "ebitda"
                    ],

                    ebitda_yoy=ebitda_yoy,

                    ebitda_qoq=ebitda_qoq,

                    ebitda_estimate=(
                        ebitda_estimate
                    ),

                    ebitda_surprise_pct=(
                        ebitda_surprise_pct
                    ),

                    ebitda_result=(
                        ebitda_result
                    ),

                    pat=current[
                        "pat"
                    ],

                    pat_yoy=pat_yoy,

                    pat_qoq=pat_qoq,

                    pat_estimate=(
                        pat_estimate
                    ),

                    pat_surprise_pct=(
                        pat_surprise_pct
                    ),

                    pat_result=(
                        pat_result
                    ),

                    eps=current[
                        "eps"
                    ],

                    eps_yoy=eps_yoy,

                    eps_estimate=(
                        eps_estimate
                    ),

                    eps_surprise_pct=(
                        eps_surprise_pct
                    ),

                    eps_result=(
                        eps_result
                    ),

                    overall_result=(
                        overall_result
                    ),

                    market_view=None,

                    summary=summary,

                    source="NSE",

                    source_url=(
                        self.nse_provider
                        .WEBSITE_URL
                        + "?symbol="
                        + symbol
                    ),

                    broadcast_date=(
                        datetime.now(
                            timezone.utc
                        )
                    ),
                )
            )

            processed.append(
                result
            )

            print(
                f"Created "
                f"{symbol} "
                f"{period}"
            )

        # =====================================================
        # Commit
        # =====================================================

        self.db.commit()

        processed.sort(
            key=lambda item: (
                item.period_ended
            ),
            reverse=True,
        )

        return processed[:limit]
