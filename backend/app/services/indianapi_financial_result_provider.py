from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class IndianAPIConsensus:
    symbol: str
    metric: str

    fiscal_year: int
    fiscal_quarter: int

    period_ended: date

    # Historical actual
    reported: Decimal | None = None

    # Historical consensus
    estimate: Decimal | None = None

    surprise_percent: Decimal | None = None

    number_of_estimates: int | None = None

    # Forward estimate
    mean: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    median: Decimal | None = None
    smart_estimate: Decimal | None = None

    is_historical: bool = False


class IndianAPIFinancialResultProvider:

    BASE_URL = (
        "https://stock.indianapi.in"
    )

    FORECAST_URL = (
        f"{BASE_URL}/stock_forecasts"
    )

    # IndianAPI measure codes
    METRICS = {
        "EPS": "eps",
        "SAL": "revenue",
        "EBT": "ebitda",
        "NET": "pat",
    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ):
        self.api_key = (
            api_key
            or settings.INDIANAPI_API_KEY
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
    # Helpers
    # =========================================================

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

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
    def to_int(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:
            return int(value)

        except Exception:
            return None

    @staticmethod
    def normalize_quarter(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        text = str(value).upper().strip()

        # QTR1
        if text.startswith("QTR"):
            text = text[3:]

        # Q1
        if text.startswith("Q"):
            text = text[1:]

        try:
            quarter = int(text)

            if quarter in (1, 2, 3, 4):
                return quarter

        except Exception:
            pass

        return None

    @staticmethod
    def fiscal_period_to_date(
        fiscal_year: int,
        fiscal_quarter: int,
    ) -> date:

        # Indian financial year:
        #
        # FY2027 Q1 -> Jun 30 2026
        # FY2027 Q2 -> Sep 30 2026
        # FY2027 Q3 -> Dec 31 2026
        # FY2027 Q4 -> Mar 31 2027
        #
        # Fiscal year is the year in which FY ends.

        if fiscal_quarter == 1:
            return date(
                fiscal_year - 1,
                6,
                30,
            )

        if fiscal_quarter == 2:
            return date(
                fiscal_year - 1,
                9,
                30,
            )

        if fiscal_quarter == 3:
            return date(
                fiscal_year - 1,
                12,
                31,
            )

        if fiscal_quarter == 4:
            return date(
                fiscal_year,
                3,
                31,
            )

        raise ValueError(
            f"Invalid fiscal quarter: "
            f"{fiscal_quarter}"
        )

    @staticmethod
    def normalize_financial_value(
        metric: str,
        value: Decimal | None,
    ) -> Decimal | None:

        if value is None:
            return None

        # IndianAPI financial estimates are
        # supplied in INR million for
        # financial statement metrics.
        #
        # StockSage database stores INR.
        #
        # EPS is already INR/share.
        if metric in {
            "revenue",
            "ebitda",
            "pat",
        }:
            return (
                value
                * Decimal("1000000")
            )

        return value

    # =========================================================
    # HTTP
    # =========================================================

    def _headers(self) -> dict[str, str]:

        if not self.api_key:
            raise RuntimeError(
                "INDIANAPI_API_KEY is not configured"
            )

        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }

    def _get(
        self,
        measure_code: str,
    ) -> dict[str, Any]:

        params = {
            "stock_id": "TCS",
            "measure_code": measure_code,
            "period_type": "Interim",
            "data_type": "Estimates",
            "age": "Current",
        }

        # stock_id is replaced by the caller
        # through _get_for_symbol().
        raise NotImplementedError

    def _get_for_symbol(
        self,
        symbol: str,
        measure_code: str,
    ) -> dict[str, Any]:

        if not self.api_key:
            raise RuntimeError(
                "INDIANAPI_API_KEY is not configured"
            )

        params = {
            "stock_id": symbol.upper(),
            "measure_code": measure_code,
            "period_type": "Interim",
            "data_type": "Estimates",
            "age": "Current",
        }

        response = self.session.get(
            self.FORECAST_URL,
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )

        if response.status_code == 401:
            raise RuntimeError(
                "IndianAPI rejected the API key "
                "(HTTP 401)"
            )

        if response.status_code == 403:
            raise RuntimeError(
                "IndianAPI denied access to "
                "stock_forecasts (HTTP 403). "
                "Check your plan/API key."
            )

        if response.status_code == 404:
            raise RuntimeError(
                "IndianAPI stock_forecasts "
                "endpoint returned HTTP 404."
            )

        response.raise_for_status()

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "IndianAPI returned non-JSON "
                "response"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Unexpected IndianAPI response"
            )

        return data

    # =========================================================
    # Response parsing
    # =========================================================

    @staticmethod
    def _find_measures(
        data: dict[str, Any],
    ) -> list[dict[str, Any]]:

        candidates = (
            data.get("measures"),
            data.get("Measures"),
            data.get("data"),
        )

        for value in candidates:

            if isinstance(value, list):
                return [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]

            if isinstance(value, dict):
                return [value]

        # Some API responses can themselves
        # represent a single measure.
        if (
            "periods" in data
            or "Periods" in data
        ):
            return [data]

        return []

    @staticmethod
    def _get_periods(
        measure: dict[str, Any],
    ) -> list[dict[str, Any]]:

        periods = (
            measure.get("periods")
            or measure.get("Periods")
            or []
        )

        if isinstance(periods, dict):
            periods = [periods]

        if not isinstance(periods, list):
            return []

        return [
            period
            for period in periods
            if isinstance(period, dict)
        ]

    def _parse_period(
        self,
        symbol: str,
        metric: str,
        period: dict[str, Any],
    ) -> IndianAPIConsensus | None:

        fiscal = (
            period.get("FiscalPeriod")
            or period.get("fiscalPeriod")
            or {}
        )

        if not isinstance(fiscal, dict):
            return None

        fiscal_year = self.to_int(
            fiscal.get("Year")
            or fiscal.get("year")
        )

        fiscal_quarter = (
            self.normalize_quarter(
                fiscal.get("Type")
                or fiscal.get("type")
            )
        )

        if (
            fiscal_year is None
            or fiscal_quarter is None
        ):
            return None

        period_ended = (
            self.fiscal_period_to_date(
                fiscal_year,
                fiscal_quarter,
            )
        )

        actuals = (
            period.get("Actuals")
            or period.get("actuals")
            or {}
        )

        estimates = (
            period.get("Estimates")
            or period.get("estimates")
            or {}
        )

        actual_list = (
            actuals.get("Actual")
            or actuals.get("actual")
            or []
        )

        estimate_list = (
            estimates.get("Estimate")
            or estimates.get("estimate")
            or []
        )

        if isinstance(
            actual_list,
            dict,
        ):
            actual_list = [actual_list]

        if isinstance(
            estimate_list,
            dict,
        ):
            estimate_list = [estimate_list]

        # -----------------------------------------------------
        # Historical result
        # -----------------------------------------------------

        if actual_list:

            actual = actual_list[0]

            if not isinstance(
                actual,
                dict,
            ):
                return None

            reported = self.to_decimal(
                actual.get("Reported")
                or actual.get("reported")
            )

            surprise_mean = self.to_decimal(
                actual.get("SurpriseMean")
                or actual.get("surpriseMean")
            )

            surprise_percent = self.to_decimal(
                actual.get(
                    "SurprisePercent"
                )
                or actual.get(
                    "surprisePercent"
                )
            )

            number_of_estimates = (
                self.to_int(
                    actual.get(
                        "NumberOfEstimates"
                    )
                    or actual.get(
                        "numberOfEstimates"
                    )
                )
            )

            reported = (
                self.normalize_financial_value(
                    metric,
                    reported,
                )
            )

            surprise_mean = (
                self.normalize_financial_value(
                    metric,
                    surprise_mean,
                )
            )

            return IndianAPIConsensus(
                symbol=symbol.upper(),
                metric=metric,
                fiscal_year=fiscal_year,
                fiscal_quarter=fiscal_quarter,
                period_ended=period_ended,
                reported=reported,
                estimate=surprise_mean,
                surprise_percent=(
                    surprise_percent
                ),
                number_of_estimates=(
                    number_of_estimates
                ),
                is_historical=True,
            )

        # -----------------------------------------------------
        # Forward estimate
        # -----------------------------------------------------

        if estimate_list:

            estimate = estimate_list[0]

            if not isinstance(
                estimate,
                dict,
            ):
                return None

            mean = self.to_decimal(
                estimate.get("Mean")
                or estimate.get("mean")
            )

            high = self.to_decimal(
                estimate.get("High")
                or estimate.get("high")
            )

            low = self.to_decimal(
                estimate.get("Low")
                or estimate.get("low")
            )

            median = self.to_decimal(
                estimate.get("Median")
                or estimate.get("median")
            )

            smart_estimate = (
                self.to_decimal(
                    estimate.get(
                        "SmartEstimate"
                    )
                    or estimate.get(
                        "smartEstimate"
                    )
                )
            )

            number_of_estimates = (
                self.to_int(
                    estimate.get(
                        "NumberOfEstimates"
                    )
                    or estimate.get(
                        "numberOfEstimates"
                    )
                )
            )

            mean = (
                self.normalize_financial_value(
                    metric,
                    mean,
                )
            )

            high = (
                self.normalize_financial_value(
                    metric,
                    high,
                )
            )

            low = (
                self.normalize_financial_value(
                    metric,
                    low,
                )
            )

            median = (
                self.normalize_financial_value(
                    metric,
                    median,
                )
            )

            smart_estimate = (
                self.normalize_financial_value(
                    metric,
                    smart_estimate,
                )
            )

            return IndianAPIConsensus(
                symbol=symbol.upper(),
                metric=metric,
                fiscal_year=fiscal_year,
                fiscal_quarter=fiscal_quarter,
                period_ended=period_ended,
                mean=mean,
                high=high,
                low=low,
                median=median,
                smart_estimate=(
                    smart_estimate
                ),
                number_of_estimates=(
                    number_of_estimates
                ),
                is_historical=False,
            )

        return None

    # =========================================================
    # Public API
    # =========================================================

    def get_metric(
        self,
        symbol: str,
        measure_code: str,
    ) -> list[IndianAPIConsensus]:

        metric = self.METRICS.get(
            measure_code.upper()
        )

        if metric is None:
            raise ValueError(
                f"Unsupported IndianAPI "
                f"measure: {measure_code}"
            )

        data = self._get_for_symbol(
            symbol,
            measure_code,
        )

        measures = self._find_measures(
            data
        )

        results: list[
            IndianAPIConsensus
        ] = []

        for measure in measures:

            periods = self._get_periods(
                measure
            )

            for period in periods:

                parsed = self._parse_period(
                    symbol,
                    metric,
                    period,
                )

                if parsed is not None:
                    results.append(parsed)

        results.sort(
            key=lambda item: item.period_ended,
            reverse=True,
        )

        return results

    def get_all(
        self,
        symbol: str,
    ) -> list[IndianAPIConsensus]:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        results: list[
            IndianAPIConsensus
        ] = []

        for measure_code in self.METRICS:

            try:

                metric_results = (
                    self.get_metric(
                        symbol,
                        measure_code,
                    )
                )

                results.extend(
                    metric_results
                )

            except Exception:
                logger.exception(
                    "IndianAPI failed for "
                    "%s / %s",
                    symbol,
                    measure_code,
                )

        return results

    def get_historical(
        self,
        symbol: str,
    ) -> list[IndianAPIConsensus]:

        return [
            item
            for item in self.get_all(symbol)
            if item.is_historical
        ]

    def get_forward(
        self,
        symbol: str,
    ) -> list[IndianAPIConsensus]:

        return [
            item
            for item in self.get_all(symbol)
            if not item.is_historical
        ]
