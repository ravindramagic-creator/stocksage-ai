from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)

from app.services.nse_financial_result_provider import (
    NSEFinancialResultProvider,
)

from app.services.indianapi_financial_result_provider import (
    IndianAPIFinancialResultProvider,
)


class FinancialResultIngestion:
    RESULT_TOLERANCE_PCT = Decimal("1.0")

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

        self.indianapi_provider = (
            IndianAPIFinancialResultProvider()
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
            (current - previous)
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
    ) -> str:

        surprise = cls.calculate_surprise(
            actual,
            estimate,
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
    # Overall result
    # =========================================================

    @staticmethod
    def calculate_overall_result(
        revenue_result: str | None,
        eps_result: str | None,
        pat_result: str | None,
        ebitda_result: str | None,
    ) -> str:

        # Revenue + EPS are the primary metrics.
        primary = [
            revenue_result,
            eps_result,
        ]

        primary = [
            value
            for value in primary
            if value in {
                "BEAT",
                "MISS",
                "MEET",
            }
        ]

        if len(primary) == 2:

            beats = primary.count("BEAT")
            misses = primary.count("MISS")

            if beats == 2:
                return "BEAT"

            if misses == 2:
                return "MISS"

        # Fall back to all available metrics.
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
    # Previous year
    # =========================================================

    @staticmethod
    def find_previous_year(
        current_period: date,
        values: dict[
            date,
            dict[str, Decimal | None],
        ],
    ):

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
                return values[
                    candidate_period
                ]

        return None

    # =========================================================
    # Ingest NSE actuals
    # =========================================================

    def ingest_nse(
        self,
        symbol: str,
        limit: int = 40,
    ) -> list:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        print(
            f"Fetching NSE financial results "
            f"for {symbol}"
        )

        provider_results = (
            self.nse_provider.get_results(
                symbol,
                limit=limit,
            )
        )

        if not provider_results:
            raise RuntimeError(
                f"NSE returned no financial "
                f"results for {symbol}"
            )

        values = {}

        for item in provider_results:

            period = item.get(
                "period_ended"
            )

            if period is None:
                continue

            values[period] = {
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

        periods = sorted(
            values.keys(),
            reverse=True,
        )

        if not periods:
            raise RuntimeError(
                f"No valid NSE periods for "
                f"{symbol}"
            )

        results = []

        for index, period in enumerate(
            periods
        ):

            current = values[period]

            previous_quarter = None

            if index + 1 < len(periods):

                previous_quarter = values[
                    periods[index + 1]
                ]

            previous_year = (
                self.find_previous_year(
                    period,
                    values,
                )
            )

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
            # Existing records MUST be updated.
            # -------------------------------------------------

            existing = (
                self.repository.get_by_period(
                    symbol,
                    period,
                )
            )

            summary_parts = []

            if revenue_yoy is not None:

                summary_parts.append(
                    f"Revenue "
                    f"{revenue_yoy:+.1f}% YoY"
                )

            if pat_yoy is not None:

                summary_parts.append(
                    f"PAT "
                    f"{pat_yoy:+.1f}% YoY"
                )

            if eps_yoy is not None:

                summary_parts.append(
                    f"EPS "
                    f"{eps_yoy:+.1f}% YoY"
                )

            if summary_parts:

                summary = (
                    ", ".join(
                        summary_parts
                    )
                    + "."
                )

            else:

                summary = (
                    "Quarterly financial "
                    "results filed with NSE."
                )

            if existing:

                # Do NOT overwrite estimates.
                existing.revenue = (
                    current["revenue"]
                )

                existing.revenue_yoy = (
                    revenue_yoy
                )

                existing.revenue_qoq = (
                    revenue_qoq
                )

                existing.ebitda = (
                    current["ebitda"]
                )

                existing.ebitda_yoy = (
                    ebitda_yoy
                )

                existing.ebitda_qoq = (
                    ebitda_qoq
                )

                existing.pat = (
                    current["pat"]
                )

                existing.pat_yoy = (
                    pat_yoy
                )

                existing.pat_qoq = (
                    pat_qoq
                )

                existing.eps = (
                    current["eps"]
                )

                existing.eps_yoy = (
                    eps_yoy
                )

                existing.summary = summary

                existing.source = "NSE"

                existing.source_url = (
                    self.nse_provider.WEBSITE_URL
                    + "?symbol="
                    + symbol
                )

                results.append(existing)

                continue

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

                    ebitda=current[
                        "ebitda"
                    ],

                    ebitda_yoy=ebitda_yoy,
                    ebitda_qoq=ebitda_qoq,

                    pat=current[
                        "pat"
                    ],

                    pat_yoy=pat_yoy,
                    pat_qoq=pat_qoq,

                    eps=current[
                        "eps"
                    ],

                    eps_yoy=eps_yoy,

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

            results.append(result)

        self.db.commit()

        return results

    # =========================================================
    # Apply IndianAPI historical consensus
    # =========================================================

    def sync_estimates(
        self,
        symbol: str,
    ) -> list:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        print(
            f"Fetching IndianAPI estimates "
            f"for {symbol}"
        )

        consensus = (
            self.indianapi_provider.get_historical(
                symbol
            )
        )

        if not consensus:

            print(
                "IndianAPI returned no "
                "historical consensus data "
                f"for {symbol}"
            )

            return []

        # -----------------------------------------------------
        # Group metrics by period
        # -----------------------------------------------------

        grouped = {}

        for item in consensus:

            if not item.is_historical:
                continue

            period = item.period_ended

            if period not in grouped:
                grouped[period] = {}

            grouped[period][
                item.metric
            ] = item

        updated = []

        for period, metrics in grouped.items():

            result = (
                self.repository.get_by_period(
                    symbol,
                    period,
                )
            )

            # If NSE doesn't have this period,
            # don't create an artificial result.
            if result is None:
                continue

            # -------------------------------------------------
            # Revenue
            # -------------------------------------------------

            revenue_item = metrics.get(
                "revenue"
            )

            if revenue_item:

                result.revenue_estimate = (
                    revenue_item.estimate
                )

                # Prefer IndianAPI's supplied
                # historical surprise.
                if (
                    revenue_item
                    .surprise_percent
                    is not None
                ):

                    result.revenue_surprise_pct = (
                        revenue_item
                        .surprise_percent
                    )

                else:

                    result.revenue_surprise_pct = (
                        self.calculate_surprise(
                            result.revenue,
                            revenue_item.estimate,
                        )
                    )

                result.revenue_result = (
                    self.classify_result(
                        result.revenue,
                        revenue_item.estimate,
                    )
                )

            # -------------------------------------------------
            # EBITDA
            # -------------------------------------------------

            ebitda_item = metrics.get(
                "ebitda"
            )

            if ebitda_item:

                result.ebitda_estimate = (
                    ebitda_item.estimate
                )

                if (
                    ebitda_item
                    .surprise_percent
                    is not None
                ):

                    result.ebitda_surprise_pct = (
                        ebitda_item
                        .surprise_percent
                    )

                else:

                    result.ebitda_surprise_pct = (
                        self.calculate_surprise(
                            result.ebitda,
                            ebitda_item.estimate,
                        )
                    )

                result.ebitda_result = (
                    self.classify_result(
                        result.ebitda,
                        ebitda_item.estimate,
                    )
                )

            # -------------------------------------------------
            # PAT
            # -------------------------------------------------

            pat_item = metrics.get(
                "pat"
            )

            if pat_item:

                result.pat_estimate = (
                    pat_item.estimate
                )

                if (
                    pat_item
                    .surprise_percent
                    is not None
                ):

                    result.pat_surprise_pct = (
                        pat_item
                        .surprise_percent
                    )

                else:

                    result.pat_surprise_pct = (
                        self.calculate_surprise(
                            result.pat,
                            pat_item.estimate,
                        )
                    )

                result.pat_result = (
                    self.classify_result(
                        result.pat,
                        pat_item.estimate,
                    )
                )

            # -------------------------------------------------
            # EPS
            # -------------------------------------------------

            eps_item = metrics.get(
                "eps"
            )

            if eps_item:

                result.eps_estimate = (
                    eps_item.estimate
                )

                if (
                    eps_item
                    .surprise_percent
                    is not None
                ):

                    result.eps_surprise_pct = (
                        eps_item
                        .surprise_percent
                    )

                else:

                    result.eps_surprise_pct = (
                        self.calculate_surprise(
                            result.eps,
                            eps_item.estimate,
                        )
                    )

                result.eps_result = (
                    self.classify_result(
                        result.eps,
                        eps_item.estimate,
                    )
                )

            # -------------------------------------------------
            # Overall
            # -------------------------------------------------

            result.overall_result = (
                self.calculate_overall_result(
                    result.revenue_result,
                    result.eps_result,
                    result.pat_result,
                    result.ebitda_result,
                )
            )

            updated.append(result)

        self.db.commit()

        print(
            f"Updated {len(updated)} "
            f"financial results with "
            f"IndianAPI estimates"
        )

        return updated

    # =========================================================
    # Main ingestion
    # =========================================================

    def ingest(
        self,
        symbol: str,
        limit: int = 40,
    ) -> list:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        # -----------------------------------------------------
        # STEP 1
        # NSE actual results
        # -----------------------------------------------------

        results = self.ingest_nse(
            symbol,
            limit,
        )

        # -----------------------------------------------------
        # STEP 2
        # IndianAPI historical estimates
        #
        # Do not fail the entire NSE sync if
        # IndianAPI is temporarily unavailable.
        # -----------------------------------------------------

        try:

            self.sync_estimates(
                symbol
            )

        except Exception as exc:

            print(
                "WARNING: IndianAPI estimate "
                f"sync failed for {symbol}: "
                f"{exc}"
            )

        # -----------------------------------------------------
        # STEP 3
        # Reload updated records.
        # -----------------------------------------------------

        self.db.expire_all()

        return self.repository.get_recent(
            symbol=symbol,
            limit=limit,
        )
