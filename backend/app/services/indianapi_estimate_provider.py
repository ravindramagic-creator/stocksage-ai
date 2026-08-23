from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class ConsensusEstimate:
    symbol: str
    metric: str

    fiscal_year: int
    fiscal_quarter: int

    calendar_year: int | None = None
    calendar_month: int | None = None

    actual_report_date: datetime | None = None

    actual: float | None = None
    estimate: float | None = None

    high: float | None = None
    low: float | None = None
    median: float | None = None
    smart_estimate: float | None = None

    surprise_mean: float | None = None
    surprise_percent: float | None = None

    number_of_estimates: int | None = None

    is_actual: bool = False


class IndianApiEstimateProvider:
    """
    Reads historical actual-vs-consensus and forward analyst estimates
    from IndianAPI.

    Historical records use:

        Actuals.Actual[].Reported
        Actuals.Actual[].SurpriseMean
        Actuals.Actual[].SurprisePercent
        Actuals.Actual[].NumberOfEstimates

    Forward records use:

        Estimates.Estimate[].Mean
        Estimates.Estimate[].High
        Estimates.Estimate[].Low
        Estimates.Estimate[].Median
        Estimates.Estimate[].SmartEstimate
        Estimates.Estimate[].NumberOfEstimates
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or settings.INDIANAPI_API_KEY
        self.base_url = (
            base_url or settings.INDIANAPI_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError(
                "INDIANAPI_API_KEY is not configured"
            )

        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_json(self, symbol: str) -> dict[str, Any]:
        """
        Fetch analyst estimates for a symbol.

        The endpoint should be changed here only if the IndianAPI
        account/version uses a different estimates endpoint.
        """

        url = f"{self.base_url}/api/v1/financials/estimates"

        response = requests.get(
            url,
            params={"symbol": symbol.upper()},
            headers=self._headers(),
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                f"Unexpected IndianAPI response for {symbol}"
            )

        return data

    @staticmethod
    def _number(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _integer(value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _quarter_from_type(
        fiscal_type: str | None,
    ) -> int | None:
        if not fiscal_type:
            return None

        value = fiscal_type.upper().replace("QTR", "")

        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> datetime | None:
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        try:
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except ValueError:
            return None

    @staticmethod
    def _measure_code_to_metric(
        measure_code: str | None,
        measure_name: str | None,
    ) -> str | None:

        code = (measure_code or "").upper()
        name = (measure_name or "").lower()

        if code == "EPS" or "earnings per share" in name:
            return "eps"

        if code in {"REVENUE", "SALES"}:
            return "revenue"

        if "revenue" in name or "sales" in name:
            return "revenue"

        if code == "EBITDA" or "ebitda" in name:
            return "ebitda"

        if code in {"NET", "NETINCOME", "PAT"}:
            return "pat"

        if "net income" in name or "profit after tax" in name:
            return "pat"

        return None

    def _parse_period(
        self,
        period: dict[str, Any],
    ) -> tuple[int | None, int | None]:
        fiscal = period.get("FiscalPeriod") or {}

        year = self._integer(
            fiscal.get("Year")
        )

        quarter = self._quarter_from_type(
            fiscal.get("Type")
        )

        return year, quarter

    def _parse_measure(
        self,
        symbol: str,
        measure: dict[str, Any],
    ) -> list[ConsensusEstimate]:

        metric = self._measure_code_to_metric(
            measure.get("measureCode"),
            measure.get("measureName"),
        )

        if metric is None:
            return []

        results: list[ConsensusEstimate] = []

        for period in measure.get("periods") or []:

            year, quarter = self._parse_period(period)

            if year is None or quarter is None:
                continue

            calendar_year = self._integer(
                period.get("CalendarYear")
            )

            calendar_month = self._integer(
                period.get("CalendarMonth")
            )

            report_date = self._parse_date(
                period.get("ActualReportDate")
            )

            actuals = period.get("Actuals") or {}
            actual_list = actuals.get("Actual") or []

            estimates = period.get("Estimates") or {}
            estimate_list = estimates.get("Estimate") or []

            actual = None

            surprise_mean = None
            surprise_percent = None
            number_of_estimates = None

            if actual_list:
                actual_item = actual_list[0]

                actual = self._number(
                    actual_item.get("Reported")
                )

                surprise_mean = self._number(
                    actual_item.get("SurpriseMean")
                )

                surprise_percent = self._number(
                    actual_item.get("SurprisePercent")
                )

                number_of_estimates = self._integer(
                    actual_item.get("NumberOfEstimates")
                )

                results.append(
                    ConsensusEstimate(
                        symbol=symbol.upper(),
                        metric=metric,
                        fiscal_year=year,
                        fiscal_quarter=quarter,
                        calendar_year=calendar_year,
                        calendar_month=calendar_month,
                        actual_report_date=report_date,
                        actual=actual,
                        estimate=surprise_mean,
                        surprise_mean=surprise_mean,
                        surprise_percent=surprise_percent,
                        number_of_estimates=number_of_estimates,
                        is_actual=True,
                    )
                )

            elif estimate_list:
                estimate_item = estimate_list[0]

                results.append(
                    ConsensusEstimate(
                        symbol=symbol.upper(),
                        metric=metric,
                        fiscal_year=year,
                        fiscal_quarter=quarter,
                        calendar_year=calendar_year,
                        calendar_month=calendar_month,
                        estimate=self._number(
                            estimate_item.get("Mean")
                        ),
                        high=self._number(
                            estimate_item.get("High")
                        ),
                        low=self._number(
                            estimate_item.get("Low")
                        ),
                        median=self._number(
                            estimate_item.get("Median")
                        ),
                        smart_estimate=self._number(
                            estimate_item.get("SmartEstimate")
                        ),
                        number_of_estimates=self._integer(
                            estimate_item.get(
                                "NumberOfEstimates"
                            )
                        ),
                        is_actual=False,
                    )
                )

        return results

    def get_estimates(
        self,
        symbol: str,
    ) -> list[ConsensusEstimate]:

        symbol = symbol.upper()

        data = self._get_json(symbol)

        measures = data.get("measures")

        if measures is None:
            measures = data.get("Measures")

        if not isinstance(measures, list):
            logger.warning(
                "IndianAPI response contains no measures for %s",
                symbol,
            )
            return []

        result: list[ConsensusEstimate] = []

        for measure in measures:
            if not isinstance(measure, dict):
                continue

            result.extend(
                self._parse_measure(
                    symbol,
                    measure,
                )
            )

        return result

    def get_historical_estimates(
        self,
        symbol: str,
    ) -> list[ConsensusEstimate]:

        return [
            item
            for item in self.get_estimates(symbol)
            if item.is_actual
        ]

    def get_forward_estimates(
        self,
        symbol: str,
    ) -> list[ConsensusEstimate]:

        return [
            item
            for item in self.get_estimates(symbol)
            if not item.is_actual
        ]
