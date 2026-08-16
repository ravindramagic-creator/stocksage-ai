from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import yfinance as yf

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import (
    FinancialResultRepository,
)


class FinancialResultIngestion:

    def __init__(self, db: Session):
        self.db = db
        self.repository = FinancialResultRepository(db)

    @staticmethod
    def yahoo_symbol(symbol: str) -> str:
        symbol = symbol.upper().strip()

        if symbol.endswith(".NS"):
            return symbol

        return f"{symbol}.NS"

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        try:
            if hasattr(value, "item"):
                value = value.item()

            return Decimal(str(value))

        except Exception:
            return None

    @staticmethod
    def to_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        try:
            if hasattr(value, "to_pydatetime"):
                value = value.to_pydatetime()

            if isinstance(value, datetime):
                return value.date()

            if isinstance(value, date):
                return value

        except Exception:
            pass

        return None

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
    def get_row(
        dataframe,
        names: list[str],
    ):

        if dataframe is None:
            return None

        # Exact match first.
        for name in names:

            if name in dataframe.index:
                return dataframe.loc[name]

        # Case-insensitive match.
        lookup = {
            str(index).strip().lower(): index
            for index in dataframe.index
        }

        for name in names:

            key = (
                name.strip().lower()
            )

            if key in lookup:
                return dataframe.loc[
                    lookup[key]
                ]

        return None

    @staticmethod
    def get_value(
        row,
        column,
    ) -> Decimal | None:

        if row is None:
            return None

        try:
            value = row[column]

        except Exception:
            return None

        return FinancialResultIngestion.to_decimal(
            value
        )

    @staticmethod
    def get_company_name(
        ticker,
        symbol: str,
    ) -> str:

        try:
            info = ticker.info

            name = (
                info.get("longName")
                or info.get("shortName")
            )

            if name:
                return str(name)

        except Exception:
            pass

        return symbol.upper()

    def ingest(
        self,
        symbol: str,
        limit: int = 8,
    ) -> list:

        symbol = symbol.upper().strip()

        yahoo_symbol = (
            self.yahoo_symbol(symbol)
        )

        print(
            f"Fetching financial results "
            f"for {yahoo_symbol}"
        )

        ticker = yf.Ticker(
            yahoo_symbol
        )

        # -------------------------------------------------
        # FETCH QUARTERLY INCOME STATEMENT
        # -------------------------------------------------

        dataframe = (
            ticker.quarterly_income_stmt
        )

        if dataframe is None:
            raise RuntimeError(
                "Yahoo returned no income statement"
            )

        if dataframe.empty:
            raise RuntimeError(
                "Yahoo returned an empty income statement"
            )

        print(
            "Yahoo financial columns:",
            list(dataframe.columns),
        )

        # -------------------------------------------------
        # FINANCIAL ROWS
        # -------------------------------------------------

        revenue_row = self.get_row(
            dataframe,
            [
                "Total Revenue",
                "Operating Revenue",
                "Revenue",
            ],
        )

        ebitda_row = self.get_row(
            dataframe,
            [
                "EBITDA",
                "Normalized EBITDA",
            ],
        )

        pat_row = self.get_row(
            dataframe,
            [
                "Net Income",
                "Net Income Common Stockholders",
                "Net Income From Continuing Operation Net Minority Interest",
            ],
        )

        eps_row = self.get_row(
            dataframe,
            [
                "Diluted EPS",
                "Basic EPS",
            ],
        )

        # Revenue is essential.
        if revenue_row is None:
            raise RuntimeError(
                "Yahoo response does not contain "
                "a revenue row"
            )

        # -------------------------------------------------
        # SORT PERIODS
        # -------------------------------------------------

        periods: list[
            tuple[Any, date]
        ] = []

        for column in dataframe.columns:

            period = self.to_date(
                column
            )

            if period is not None:
                periods.append(
                    (
                        column,
                        period,
                    )
                )

        periods.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        periods = periods[:limit]

        if not periods:
            raise RuntimeError(
                "No valid financial periods "
                "returned by Yahoo"
            )

        # -------------------------------------------------
        # READ ALL PERIOD VALUES
        # -------------------------------------------------

        values: dict[
            date,
            dict[str, Decimal | None],
        ] = {}

        for column, period in periods:

            values[period] = {
                "revenue":
                    self.get_value(
                        revenue_row,
                        column,
                    ),

                "ebitda":
                    self.get_value(
                        ebitda_row,
                        column,
                    ),

                "pat":
                    self.get_value(
                        pat_row,
                        column,
                    ),

                "eps":
                    self.get_value(
                        eps_row,
                        column,
                    ),
            }

        # -------------------------------------------------
        # COMPANY NAME
        # -------------------------------------------------

        company_name = (
            self.get_company_name(
                ticker,
                symbol,
            )
        )

        results = []

        # -------------------------------------------------
        # CREATE / UPDATE RESULTS
        # -------------------------------------------------

        for index, (
            column,
            period,
        ) in enumerate(periods):

            current = values[period]

            # Previous quarter.
            previous_quarter = None

            if index + 1 < len(periods):

                previous_period = periods[
                    index + 1
                ][1]

                previous_quarter = values[
                    previous_period
                ]

            # -------------------------------------------------
            # YOY
            #
            # Find a period approximately 12 months
            # earlier instead of assuming index + 4.
            # -------------------------------------------------

            previous_year = None

            for candidate_period in values:

                days_difference = (
                    period - candidate_period
                ).days

                if (
                    330
                    <= days_difference
                    <= 400
                ):
                    previous_year = values[
                        candidate_period
                    ]
                    break

            revenue_yoy = (
                self.calculate_growth(
                    current["revenue"],
                    previous_year[
                        "revenue"
                    ]
                    if previous_year
                    else None,
                )
            )

            revenue_qoq = (
                self.calculate_growth(
                    current["revenue"],
                    previous_quarter[
                        "revenue"
                    ]
                    if previous_quarter
                    else None,
                )
            )

            ebitda_yoy = (
                self.calculate_growth(
                    current["ebitda"],
                    previous_year[
                        "ebitda"
                    ]
                    if previous_year
                    else None,
                )
            )

            ebitda_qoq = (
                self.calculate_growth(
                    current["ebitda"],
                    previous_quarter[
                        "ebitda"
                    ]
                    if previous_quarter
                    else None,
                )
            )

            pat_yoy = (
                self.calculate_growth(
                    current["pat"],
                    previous_year[
                        "pat"
                    ]
                    if previous_year
                    else None,
                )
            )

            pat_qoq = (
                self.calculate_growth(
                    current["pat"],
                    previous_quarter[
                        "pat"
                    ]
                    if previous_quarter
                    else None,
                )
            )

            eps_yoy = (
                self.calculate_growth(
                    current["eps"],
                    previous_year[
                        "eps"
                    ]
                    if previous_year
                    else None,
                )
            )

            # -------------------------------------------------
            # CHECK EXISTING RECORD
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
            # SUMMARY
            # -------------------------------------------------

            summary_parts = []

            if revenue_yoy is not None:

                summary_parts.append(
                    f"Revenue "
                    f"{revenue_yoy:+.1f}% YoY"
                )

            if ebitda_yoy is not None:

                summary_parts.append(
                    f"EBITDA "
                    f"{ebitda_yoy:+.1f}% YoY"
                )

            if pat_yoy is not None:

                summary_parts.append(
                    f"PAT "
                    f"{pat_yoy:+.1f}% YoY"
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
                    "results available."
                )

            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------

            result = (
                self.repository.create(
                    symbol=symbol,
                    company_name=company_name,
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

                    pat=current["pat"],

                    pat_yoy=pat_yoy,
                    pat_qoq=pat_qoq,

                    eps=current["eps"],

                    eps_yoy=eps_yoy,

                    market_view=None,

                    summary=summary,

                    source="Yahoo Finance",

                    source_url=(
                        "https://finance.yahoo.com/"
                        f"quote/{yahoo_symbol}/"
                        "financials/"
                    ),

                    broadcast_date=datetime.now(
                        timezone.utc
                    ),
                )
            )

            results.append(
                result
            )

        # Commit once after all records.
        self.db.commit()

        print(
            f"Stored {len(results)} "
            f"financial results for {symbol}"
        )

        return results
