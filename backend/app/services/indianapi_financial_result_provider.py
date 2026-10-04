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

    # Historical reported value and analyst consensus.
    reported: Decimal | None = None
    estimate: Decimal | None = None
    surprise_percent: Decimal | None = None
    number_of_estimates: int | None = None

    # Forward consensus range.
    mean: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    median: Decimal | None = None
    smart_estimate: Decimal | None = None

    is_historical: bool = False


class IndianAPIFinancialResultProvider:
    """IndianAPI provider for historical and forward analyst consensus.

    Important distinction:

    * data_type=Actuals contains reported historical periods and, where
      available, the historical consensus used to calculate the surprise.
    * data_type=Estimates contains forward analyst forecasts.

    The previous implementation always requested data_type=Estimates and then
    filtered for is_historical=True. That combination meant historical
    consensus was normally discarded, leaving every quarter without an
    estimate and therefore without a meaningful BEAT/MISS calculation.
    """

    BASE_URL = "https://stock.indianapi.in"
    FORECAST_URL = f"{BASE_URL}/stock_forecasts"

    # IndianAPI measure codes.
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
        self.api_key = api_key or settings.INDIANAPI_API_KEY
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "StockSage-AI/1.0",
            }
        )

    # =========================================================
    # Scalar helpers
    # =========================================================

    @staticmethod
    def to_decimal(value: Any) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            text = str(value).strip().replace(",", "")
            if not text:
                return None
            return Decimal(text)
        except Exception:
            return None

    @staticmethod
    def to_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except Exception:
            return None

    @staticmethod
    def normalize_quarter(value: Any) -> int | None:
        if value is None:
            return None

        text = str(value).upper().strip()
        for prefix in ("QTR", "Q"):
            if text.startswith(prefix):
                text = text[len(prefix) :]
                break

        try:
            quarter = int(text)
            return quarter if quarter in (1, 2, 3, 4) else None
        except Exception:
            return None

    @staticmethod
    def fiscal_period_to_date(
        fiscal_year: int,
        fiscal_quarter: int,
    ) -> date:
        # FY2027 Q1 = Jun-2026, Q2 = Sep-2026,
        # Q3 = Dec-2026, Q4 = Mar-2027.
        if fiscal_quarter == 1:
            return date(fiscal_year - 1, 6, 30)
        if fiscal_quarter == 2:
            return date(fiscal_year - 1, 9, 30)
        if fiscal_quarter == 3:
            return date(fiscal_year - 1, 12, 31)
        if fiscal_quarter == 4:
            return date(fiscal_year, 3, 31)
        raise ValueError(f"Invalid fiscal quarter: {fiscal_quarter}")

    @staticmethod
    def normalize_financial_value(
        metric: str,
        value: Decimal | None,
    ) -> Decimal | None:
        if value is None:
            return None

        # IndianAPI reports financial-statement values in INR millions.
        # StockSage stores these values in INR. EPS is already INR/share.
        if metric in {"revenue", "ebitda", "pat"}:
            return value * Decimal("1000000")

        return value

    # =========================================================
    # HTTP
    # =========================================================

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("INDIANAPI_API_KEY is not configured")
        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }

    def _get_for_symbol(
        self,
        symbol: str,
        measure_code: str,
        data_type: str,
        age: str = "Current",
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("INDIANAPI_API_KEY is not configured")

        params = {
            "stock_id": symbol.upper(),
            "measure_code": measure_code,
            "period_type": "Interim",
            "data_type": data_type,
            "age": age,
        }

        response = self.session.get(
            self.FORECAST_URL,
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )

        if response.status_code == 401:
            raise RuntimeError("IndianAPI rejected the API key (HTTP 401)")
        if response.status_code == 403:
            raise RuntimeError(
                "IndianAPI denied access to stock_forecasts (HTTP 403). "
                "Check your plan/API key."
            )
        if response.status_code == 404:
            raise RuntimeError("IndianAPI stock_forecasts returned HTTP 404")

        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError("IndianAPI returned non-JSON response") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Unexpected IndianAPI response")

        return data

    # =========================================================
    # Response parsing
    # =========================================================

    @staticmethod
    def _find_measures(data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("measures", "Measures", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                return [value]

        if "periods" in data or "Periods" in data:
            return [data]

        return []

    @staticmethod
    def _get_periods(measure: dict[str, Any]) -> list[dict[str, Any]]:
        periods = measure.get("periods") or measure.get("Periods") or []
        if isinstance(periods, dict):
            periods = [periods]
        if not isinstance(periods, list):
            return []
        return [period for period in periods if isinstance(period, dict)]

    @staticmethod
    def _first_dict(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    return item
        return None

    def _period_identity(
        self,
        period: dict[str, Any],
    ) -> tuple[int, int, date] | None:
        fiscal = period.get("FiscalPeriod") or period.get("fiscalPeriod") or {}
        if not isinstance(fiscal, dict):
            return None

        fiscal_year = self.to_int(fiscal.get("Year") or fiscal.get("year"))
        fiscal_quarter = self.normalize_quarter(
            fiscal.get("Type") or fiscal.get("type")
        )

        if fiscal_year is None or fiscal_quarter is None:
            return None

        return (
            fiscal_year,
            fiscal_quarter,
            self.fiscal_period_to_date(fiscal_year, fiscal_quarter),
        )

    def _parse_actual_period(
        self,
        symbol: str,
        metric: str,
        period: dict[str, Any],
    ) -> IndianAPIConsensus | None:
        identity = self._period_identity(period)
        if identity is None:
            return None

        fiscal_year, fiscal_quarter, period_ended = identity

        actuals = period.get("Actuals") or period.get("actuals") or {}
        actual = self._first_dict(
            actuals.get("Actual") or actuals.get("actual")
        )

        if actual is None:
            return None

        reported = self.to_decimal(
            actual.get("Reported") or actual.get("reported")
        )

        # Historical consensus is supplied by IndianAPI as SurpriseMean on
        # the actual-period record. Support common aliases as well.
        estimate = self.to_decimal(
            actual.get("SurpriseMean")
            or actual.get("surpriseMean")
            or actual.get("MeanEstimate")
            or actual.get("meanEstimate")
            or actual.get("Consensus")
            or actual.get("consensus")
        )

        surprise_percent = self.to_decimal(
            actual.get("SurprisePercent")
            or actual.get("surprisePercent")
        )

        number_of_estimates = self.to_int(
            actual.get("NumberOfEstimates")
            or actual.get("numberOfEstimates")
        )

        return IndianAPIConsensus(
            symbol=symbol.upper(),
            metric=metric,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            period_ended=period_ended,
            reported=self.normalize_financial_value(metric, reported),
            estimate=self.normalize_financial_value(metric, estimate),
            surprise_percent=surprise_percent,
            number_of_estimates=number_of_estimates,
            is_historical=True,
        )

    def _parse_estimate_period(
        self,
        symbol: str,
        metric: str,
        period: dict[str, Any],
    ) -> IndianAPIConsensus | None:
        identity = self._period_identity(period)
        if identity is None:
            return None

        fiscal_year, fiscal_quarter, period_ended = identity
        estimates = period.get("Estimates") or period.get("estimates") or {}
        estimate = self._first_dict(
            estimates.get("Estimate") or estimates.get("estimate")
        )

        if estimate is None:
            return None

        def value(*names: str) -> Decimal | None:
            for name in names:
                parsed = self.to_decimal(estimate.get(name))
                if parsed is not None:
                    return parsed
            return None

        return IndianAPIConsensus(
            symbol=symbol.upper(),
            metric=metric,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            period_ended=period_ended,
            mean=self.normalize_financial_value(
                metric,
                value("Mean", "mean", "Consensus", "consensus"),
            ),
            high=self.normalize_financial_value(metric, value("High", "high")),
            low=self.normalize_financial_value(metric, value("Low", "low")),
            median=self.normalize_financial_value(
                metric,
                value("Median", "median"),
            ),
            smart_estimate=self.normalize_financial_value(
                metric,
                value("SmartEstimate", "smartEstimate"),
            ),
            number_of_estimates=self.to_int(
                estimate.get("NumberOfEstimates")
                or estimate.get("numberOfEstimates")
            ),
            is_historical=False,
        )

    # =========================================================
    # Public API
    # =========================================================

    def get_metric(
        self,
        symbol: str,
        measure_code: str,
        data_type: str = "Actuals",
    ) -> list[IndianAPIConsensus]:
        metric = self.METRICS.get(measure_code.upper())
        if metric is None:
            raise ValueError(f"Unsupported IndianAPI measure: {measure_code}")

        if data_type not in {"Actuals", "Estimates"}:
            raise ValueError(f"Unsupported IndianAPI data type: {data_type}")

        data = self._get_for_symbol(
            symbol,
            measure_code,
            data_type=data_type,
        )

        results: list[IndianAPIConsensus] = []
        for measure in self._find_measures(data):
            for period in self._get_periods(measure):
                if data_type == "Actuals":
                    parsed = self._parse_actual_period(
                        symbol,
                        metric,
                        period,
                    )
                else:
                    parsed = self._parse_estimate_period(
                        symbol,
                        metric,
                        period,
                    )

                if parsed is not None:
                    results.append(parsed)

        results.sort(key=lambda item: item.period_ended, reverse=True)
        return results

    def get_all(self, symbol: str) -> list[IndianAPIConsensus]:
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        results: list[IndianAPIConsensus] = []
        for measure_code in self.METRICS:
            try:
                results.extend(self.get_metric(symbol, measure_code, "Actuals"))
                results.extend(self.get_metric(symbol, measure_code, "Estimates"))
            except Exception:
                logger.exception(
                    "IndianAPI failed for %s / %s",
                    symbol,
                    measure_code,
                )
        return results

    def get_historical(self, symbol: str) -> list[IndianAPIConsensus]:
        """Return historical quarters with their original consensus estimate.

        This intentionally uses data_type=Actuals. IndianAPI associates the
        historical analyst consensus with the reported actual period, which is
        what is required to calculate a genuine earnings surprise.
        """
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        results: list[IndianAPIConsensus] = []
        for measure_code in self.METRICS:
            try:
                results.extend(
                    self.get_metric(symbol, measure_code, "Actuals")
                )
            except Exception:
                logger.exception(
                    "IndianAPI historical consensus failed for %s / %s",
                    symbol,
                    measure_code,
                )

        # One metric/period should occur only once. Keep the record with an
        # actual consensus estimate when duplicate provider records exist.
        deduped: dict[tuple[str, date], IndianAPIConsensus] = {}
        for item in results:
            key = (item.metric, item.period_ended)
            existing = deduped.get(key)
            if existing is None or (
                existing.estimate is None and item.estimate is not None
            ):
                deduped[key] = item

        return sorted(
            deduped.values(),
            key=lambda item: item.period_ended,
            reverse=True,
        )

    def get_forward(self, symbol: str) -> list[IndianAPIConsensus]:
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        results: list[IndianAPIConsensus] = []
        for measure_code in self.METRICS:
            try:
                results.extend(
                    self.get_metric(symbol, measure_code, "Estimates")
                )
            except Exception:
                logger.exception(
                    "IndianAPI forward consensus failed for %s / %s",
                    symbol,
                    measure_code,
                )

        return sorted(
            results,
            key=lambda item: item.period_ended,
        )
