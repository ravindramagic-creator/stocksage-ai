from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import requests


class AnalystEstimateProvider:
    """
    Analyst consensus estimate provider using IndianAPI.

    ACTUAL financial results:
        NSE

    ANALYST estimates:
        IndianAPI /stock_forecasts

    IndianAPI measure codes:

        SAL -> Revenue
        EPS -> Earnings Per Share
        EBT -> EBITDA
        NET -> Net Income / PAT

    Required IndianAPI parameters:

        stock_id
        measure_code
        period_type
        data_type
        age

    We never invent an estimate.

    If IndianAPI does not provide an estimate for a
    particular period, the value remains None.
    """

    BASE_URL = "https://stock.indianapi.in"

    FORECAST_URL = (
        f"{BASE_URL}/stock_forecasts"
    )

    DEFAULT_TIMEOUT = 20

    MEASURES = {
        "SAL": "revenue_estimate",
        "EPS": "eps_estimate",
        "EBT": "ebitda_estimate",
        "NET": "pat_estimate",
    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.api_key = (
            api_key
            or os.getenv(
                "INDIANAPI_API_KEY"
            )
        )

        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "StockSage-AI/1.0"
                ),
            }
        )

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

        if isinstance(
            value,
            bool,
        ):
            return None

        text = str(value).strip()

        if not text:
            return None

        text = (
            text
            .replace(",", "")
            .replace("₹", "")
            .replace("%", "")
        )

        if text.lower() in {
            "none",
            "null",
            "n/a",
            "na",
            "-",
            "--",
            "nan",
            "nil",
        }:
            return None

        try:
            return Decimal(text)

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
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%b %Y",
            "%B %Y",
        )

        for fmt in formats:

            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:
                continue

        # ISO timestamp

        try:

            return datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            ).date()

        except Exception:
            pass

        return None

    # =========================================================
    # API request
    # =========================================================

    def _get_forecast(
        self,
        symbol: str,
        measure_code: str,
    ) -> Any:

        if not self.api_key:

            print(
                "INDIANAPI_API_KEY is not configured. "
                "Analyst estimates will remain unavailable."
            )

            return None

        params = {
            "stock_id": symbol.upper(),
            "measure_code": measure_code,
            "period_type": "Interim",
            "data_type": "Estimates",
            "age": "Current",
        }

        try:

            response = self.session.get(
                self.FORECAST_URL,
                params=params,
                timeout=self.timeout,
                headers={
                    "X-Api-Key": self.api_key,
                },
            )

            if response.status_code == 404:

                print(
                    f"IndianAPI: no forecast found "
                    f"for {symbol} "
                    f"measure={measure_code}"
                )

                return None

            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            return data

        except requests.RequestException as exc:

            print(
                f"IndianAPI request failed: "
                f"symbol={symbol}, "
                f"measure={measure_code}, "
                f"error={exc}"
            )

            return None

        except Exception as exc:

            print(
                f"IndianAPI response parsing failed: "
                f"symbol={symbol}, "
                f"measure={measure_code}, "
                f"error={exc}"
            )

            return None

    # =========================================================
    # Recursive dictionary traversal
    # =========================================================

    @classmethod
    def walk(
        cls,
        value: Any,
    ):

        if isinstance(
            value,
            dict,
        ):

            yield value

            for child in value.values():

                yield from cls.walk(
                    child
                )

        elif isinstance(
            value,
            list,
        ):

            for child in value:

                yield from cls.walk(
                    child
                )

    # =========================================================
    # Find date
    # =========================================================

    @classmethod
    def find_period(
        cls,
        obj: dict[str, Any],
    ) -> date | None:

        keys = (
            "period",
            "period_end",
            "periodEnded",
            "period_ended",
            "periodEnd",
            "fiscalDateEnding",
            "fiscal_date_ending",
            "fiscalPeriodEnd",
            "fiscal_period_end",
            "date",
            "endDate",
            "end_date",
            "forecastDate",
            "forecast_date",
        )

        for key in keys:

            if key not in obj:
                continue

            parsed = cls.to_date(
                obj.get(key)
            )

            if parsed:
                return parsed

        return None

    # =========================================================
    # Find numeric value
    # =========================================================

    @classmethod
    def find_value(
        cls,
        obj: dict[str, Any],
    ) -> Decimal | None:

        keys = (
            "value",
            "Value",
            "estimate",
            "Estimate",
            "estimatedValue",
            "estimated_value",
            "forecast",
            "Forecast",
            "mean",
            "Mean",
            "median",
            "Median",
            "consensus",
            "Consensus",
            "consensusEstimate",
            "consensus_estimate",
            "consensusMean",
            "consensus_mean",
            "actual",
        )

        for key in keys:

            if key not in obj:
                continue

            value = cls.to_decimal(
                obj.get(key)
            )

            if value is not None:
                return value

        return None

    # =========================================================
    # Extract records
    # =========================================================

    @classmethod
    def extract_records(
        cls,
        payload: Any,
    ) -> list[
        tuple[date, Decimal]
    ]:

        records = []

        for obj in cls.walk(
            payload
        ):

            if not isinstance(
                obj,
                dict,
            ):
                continue

            period = cls.find_period(
                obj
            )

            value = cls.find_value(
                obj
            )

            if (
                period is None
                or value is None
            ):
                continue

            records.append(
                (
                    period,
                    value,
                )
            )

        # Deduplicate by period.

        unique: dict[
            date,
            Decimal,
        ] = {}

        for period, value in records:

            unique[period] = value

        return list(
            unique.items()
        )

    # =========================================================
    # Get normalized estimates
    # =========================================================

    def get_normalized_estimates(
        self,
        symbol: str,
    ) -> dict[
        date,
        dict[str, Decimal | None],
    ]:

        symbol = (
            symbol.upper()
            .strip()
        )

        result: dict[
            date,
            dict[str, Decimal | None],
        ] = {}

        if not symbol:
            return result

        for measure_code, field_name in (
            self.MEASURES.items()
        ):

            payload = (
                self._get_forecast(
                    symbol,
                    measure_code,
                )
            )

            if payload is None:
                continue

            records = (
                self.extract_records(
                    payload
                )
            )

            print(
                f"IndianAPI "
                f"{measure_code}: "
                f"{len(records)} records"
            )

            for period, value in records:

                if period not in result:

                    result[period] = {
                        "revenue_estimate": None,
                        "ebitda_estimate": None,
                        "pat_estimate": None,
                        "eps_estimate": None,
                    }

                result[period][
                    field_name
                ] = value

        print(
            f"IndianAPI normalized "
            f"{len(result)} estimate periods "
            f"for {symbol}"
        )

        return result
