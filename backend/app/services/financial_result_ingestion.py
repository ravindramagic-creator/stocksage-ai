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


class FinancialResultIngestion:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.repository = (
            FinancialResultRepository(db)
        )

        self.provider = (
            NSEFinancialResultProvider()
        )

    # ---------------------------------------------------------
    # Growth
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Period matching
    # ---------------------------------------------------------

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
                return values[candidate_period]

        return None

    # ---------------------------------------------------------
    # Ingest
    # ---------------------------------------------------------

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

        print(
            f"Fetching NSE financial results "
            f"for {symbol}"
        )

        provider_results = (
            self.provider.get_results(
                symbol,
                limit=limit,
            )
        )

        if not provider_results:
            raise RuntimeError(
                f"NSE returned no financial "
                f"results for {symbol}"
            )

        # -----------------------------------------------------
        # Convert to period dictionary
        # -----------------------------------------------------

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
                f"NSE returned no valid "
                f"financial periods for {symbol}"
            )

        results = []

        # -----------------------------------------------------
        # Process each quarter
        # -----------------------------------------------------

        for index, period in enumerate(
            periods
        ):

            current = values[period]

            previous_quarter = None

            if index + 1 < len(periods):

                previous_period = periods[
                    index + 1
                ]

                previous_quarter = (
                    values[
                        previous_period
                    ]
                )

            previous_year = (
                self.find_previous_year(
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
            # Existing record
            # -------------------------------------------------

            existing = (
                self.repository.get_by_period(
                    symbol,
                    period,
                )
            )

            if existing:

                results.append(
                    existing
                )

                continue

            # -------------------------------------------------
            # Summary
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Save
            # -------------------------------------------------

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
                        self.provider.WEBSITE_URL
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

            results.append(
                result
            )

        self.db.commit()

        print(
            f"Stored {len(results)} "
            f"NSE financial results "
            f"for {symbol}"
        )

        return results
