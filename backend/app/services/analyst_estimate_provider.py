from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import requests


class AnalystEstimateProvider:
    """
    Analyst consensus estimate provider.

    IMPORTANT:

    NSE remains the source of ACTUAL financial results.

    This provider is only for analyst consensus estimates.

    Supported estimates:
        - EPS
        - Revenue

    Alpha Vantage provides an EARNINGS_ESTIMATES endpoint
    for quarterly and annual EPS/revenue estimates.

    If estimates are unavailable, this provider returns
    empty values rather than inventing numbers.
    """

    BASE_URL = (
        "https://www.alphavantage.co/query"
    )

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 20,
    ):

        self.api_key = (
            api_key
            or os.getenv(
                "ALPHAVANTAGE_API_KEY"
            )
        )

        self.timeout = timeout

    # =========================================================
    # Decimal
    # =========================================================

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        if isinstance(
            value,
            Decimal,
        ):
            return value

        text = str(value).strip()

        if not text:
            return None

        if text.lower() in {
            "none",
            "null",
            "n/a",
            "na",
            "-",
            "--",
        }:
            return None

        try:

            return Decimal(
                text.replace(",", "")
            )

        except Exception:

            return None

    # =========================================================
    # Date
    # =========================================================

    @staticmethod
    def to_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        text = str(value).strip()

        if not text:
            return None

        formats = (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
        )

        for fmt in formats:

            try:

                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:
                continue

        return None

    # =========================================================
    # API request
    # =========================================================

    def _get(
        self,
        function: str,
        symbol: str,
    ) -> dict[str, Any]:

        if not self.api_key:

            print(
                "ALPHAVANTAGE_API_KEY is not configured. "
                "Analyst estimates will remain unavailable."
            )

            return {}

        response = requests.get(
            self.BASE_URL,
            params={
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(
            data,
            dict,
        ):
            return {}

        if (
            "Note" in data
            or "Information" in data
        ):

            print(
                f"Alpha Vantage message: "
                f"{data.get('Note') or data.get('Information')}"
            )

            return {}

        return data

    # =========================================================
    # Symbol candidates
    # =========================================================

    @staticmethod
    def symbol_candidates(
        symbol: str,
    ) -> list[str]:

        symbol = symbol.upper().strip()

        candidates = [
            symbol,
            f"{symbol}.BSE",
            f"{symbol}.NSE",
        ]

        # Remove duplicates while preserving order.

        return list(
            dict.fromkeys(
                candidates
            )
        )

    # =========================================================
    # Earnings estimates
    # =========================================================

    def get_estimates(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:

        for candidate in self.symbol_candidates(
            symbol
        ):

            try:

                data = self._get(
                    "EARNINGS_ESTIMATES",
                    candidate,
                )

                rows = data.get(
                    "estimates",
                    [],
                )

                if (
                    isinstance(
                        rows,
                        list,
                    )
                    and rows
                ):

                    return rows

            except Exception as exc:

                print(
                    f"Failed to fetch estimates "
                    f"for {candidate}: {exc}"
                )

        return []

    # =========================================================
    # Normalize estimates
    # =========================================================

    def get_normalized_estimates(
        self,
        symbol: str,
    ) -> dict[
        date,
        dict[str, Decimal | None],
    ]:

        rows = self.get_estimates(
            symbol
        )

        result: dict[
            date,
            dict[str, Decimal | None],
        ] = {}

        for row in rows:

            if not isinstance(
                row,
                dict,
            ):
                continue

            period = self.to_date(
                row.get(
                    "fiscalDateEnding"
                )
            )

            if period is None:
                continue

            # -------------------------------------------------
            # Alpha Vantage fields can vary slightly.
            # Try the common names.
            # -------------------------------------------------

            eps_estimate = (
                self.to_decimal(
                    row.get(
                        "estimatedEPS"
                    )
                    or row.get(
                        "estimatedEps"
                    )
                    or row.get(
                        "epsEstimate"
                    )
                )
            )

            revenue_estimate = (
                self.to_decimal(
                    row.get(
                        "estimatedRevenue"
                    )
                    or row.get(
                        "estimatedRevenueMedian"
                    )
                    or row.get(
                        "revenueEstimate"
                    )
                )
            )

            result[period] = {
                "eps_estimate": (
                    eps_estimate
                ),
                "revenue_estimate": (
                    revenue_estimate
                ),
            }

        return result
