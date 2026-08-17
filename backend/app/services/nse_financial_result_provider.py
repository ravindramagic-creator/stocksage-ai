from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import requests


class NSEFinancialResultProvider:
    """
    NSE provider for official quarterly financial results.

    Uses NSE's corporate financial-results endpoints.

    Primary numeric source:
        /api/results-comparision

    Metadata source:
        /api/corporate-financial-results

    NSE monetary values are generally returned in INR lakhs
    by the results comparison endpoint.
    """

    BASE_URL = "https://www.nseindia.com"

    RESULTS_COMPARISON_URL = (
        f"{BASE_URL}/api/results-comparision"
    )

    FINANCIAL_RESULTS_URL = (
        f"{BASE_URL}/api/corporate-financial-results"
    )

    WEBSITE_URL = (
        f"{BASE_URL}/companies-listing/"
        "corporate-filings-financial-results"
    )

    def __init__(
        self,
        timeout: int = 20,
    ):
        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/130.0 Safari/537.36"
                ),
                "Accept": (
                    "application/json,"
                    "text/plain,*/*"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": self.BASE_URL + "/",
                "Connection": "keep-alive",
            }
        )

    # ---------------------------------------------------------
    # Generic helpers
    # ---------------------------------------------------------

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        if isinstance(value, Decimal):
            return value

        if isinstance(value, bool):
            return None

        try:
            text = str(value).strip()

            if not text:
                return None

            text = text.replace(",", "")

            return Decimal(text)

        except Exception:
            return None

    @staticmethod
    def to_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value).strip()

        if not text:
            return None

        formats = (
            "%d-%b-%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
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

    @staticmethod
    def first_value(
        row: dict,
        keys: tuple[str, ...],
    ) -> Any:

        for key in keys:

            value = row.get(key)

            if value is not None:
                return value

        return None

    # ---------------------------------------------------------
    # NSE request
    # ---------------------------------------------------------

    def _get(
        self,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        if response.status_code == 401:
            raise RuntimeError(
                "NSE rejected the request "
                "(HTTP 401)"
            )

        if response.status_code == 403:
            raise RuntimeError(
                "NSE rejected the request "
                "(HTTP 403)"
            )

        response.raise_for_status()

        try:
            return response.json()

        except ValueError as exc:
            raise RuntimeError(
                "NSE returned a non-JSON response"
            ) from exc

    # ---------------------------------------------------------
    # Results comparison
    # ---------------------------------------------------------

    def get_results_comparison(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "NSE symbol cannot be empty"
            )

        data = self._get(
            self.RESULTS_COMPARISON_URL,
            {
                "symbol": symbol,
            },
        )

        rows = data.get(
            "resCmpData",
            [],
        )

        if not isinstance(rows, list):
            return []

        return rows

    # ---------------------------------------------------------
    # Financial-result filing metadata
    # ---------------------------------------------------------

    def get_financial_result_filings(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:

        symbol = symbol.upper().strip()

        data = self._get(
            self.FINANCIAL_RESULTS_URL,
            {
                "index": "equities",
                "symbol": symbol,
                "period": "quarterly",
                "limit": 20,
            },
        )

        rows = data.get(
            "data",
            [],
        )

        if not isinstance(rows, list):
            return []

        return rows

    # ---------------------------------------------------------
    # Convert NSE comparison row
    # ---------------------------------------------------------

    def parse_result_row(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:

        # NSE results comparison reports monetary
        # figures in INR lakhs.

        total_income = self.to_decimal(
            self.first_value(
                row,
                (
                    "re_total_inc",
                    "re_total_income",
                    "totalIncome",
                ),
            )
        )

        net_profit = self.to_decimal(
            self.first_value(
                row,
                (
                    "re_net_profit",
                    "re_net_profit_loss",
                    "netProfit",
                ),
            )
        )

        eps = self.to_decimal(
            self.first_value(
                row,
                (
                    "re_eps",
                    "re_eps_diluted",
                    "eps",
                ),
            )
        )

        period_ended = self.to_date(
            self.first_value(
                row,
                (
                    "re_to_dt",
                    "toDate",
                    "periodEnded",
                ),
            )
        )

        period_from = self.to_date(
            self.first_value(
                row,
                (
                    "re_from_dt",
                    "fromDate",
                    "periodFrom",
                ),
            )
        )

        return {
            "period_ended": period_ended,
            "period_from": period_from,

            # Convert INR lakhs -> INR.
            "revenue": (
                total_income * Decimal("100000")
                if total_income is not None
                else None
            ),

            "pat": (
                net_profit * Decimal("100000")
                if net_profit is not None
                else None
            ),

            "eps": eps,

            # NSE comparison endpoint does not
            # reliably expose EBITDA.
            "ebitda": None,

            "raw": row,
        }

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def get_results(
        self,
        symbol: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:

        rows = self.get_results_comparison(
            symbol,
        )

        results = []

        for row in rows:

            if not isinstance(row, dict):
                continue

            parsed = self.parse_result_row(
                row,
            )

            if parsed["period_ended"] is None:
                continue

            results.append(parsed)

        results.sort(
            key=lambda item: item["period_ended"],
            reverse=True,
        )

        return results[:limit]
