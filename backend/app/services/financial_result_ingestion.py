from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import FinancialResultRepository
from app.services.nse_financial_result_provider import NSEFinancialResultProvider
from app.services.indianapi_financial_result_provider import IndianAPIFinancialResultProvider


class FinancialResultIngestion:
    RESULT_TOLERANCE_PCT = Decimal("1.0")

    def __init__(self, db: Session):
        self.db = db
        self.repository = FinancialResultRepository(db)
        self.nse_provider = NSEFinancialResultProvider()
        self.indianapi_provider = IndianAPIFinancialResultProvider()

    @staticmethod
    def calculate_growth(current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous is None or previous == 0:
            return None
        return ((current - previous) / abs(previous)) * Decimal("100")

    @staticmethod
    def calculate_surprise(actual: Decimal | None, estimate: Decimal | None) -> Decimal | None:
        if actual is None or estimate is None or estimate == 0:
            return None
        return ((actual - estimate) / abs(estimate)) * Decimal("100")

    @classmethod
    def classify_result(cls, actual: Decimal | None, estimate: Decimal | None) -> str:
        surprise = cls.calculate_surprise(actual, estimate)
        if surprise is None:
            return "UNKNOWN"
        if surprise > cls.RESULT_TOLERANCE_PCT:
            return "BEAT"
        if surprise < -cls.RESULT_TOLERANCE_PCT:
            return "MISS"
        return "MEET"

    @staticmethod
    def calculate_overall_result(
        revenue_result: str | None,
        eps_result: str | None,
        pat_result: str | None,
        ebitda_result: str | None,
    ) -> str:
        primary = [
            value for value in (revenue_result, eps_result)
            if value in {"BEAT", "MISS", "MEET"}
        ]
        if len(primary) == 2:
            if primary.count("BEAT") == 2:
                return "BEAT"
            if primary.count("MISS") == 2:
                return "MISS"

        results = [
            value
            for value in (revenue_result, eps_result, pat_result, ebitda_result)
            if value in {"BEAT", "MISS", "MEET"}
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

    @staticmethod
    def find_previous_year(
        current_period: date,
        values: dict[date, dict[str, Decimal | None]],
    ):
        for candidate_period in values:
            days_difference = (current_period - candidate_period).days
            if 330 <= days_difference <= 400:
                return values[candidate_period]
        return None

    def ingest_nse(self, symbol: str, limit: int = 40) -> list:
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        print(f"Fetching NSE financial results for {symbol}")
        provider_results = self.nse_provider.get_results(symbol, limit=limit)
        if not provider_results:
            raise RuntimeError(f"NSE returned no financial results for {symbol}")

        values = {}
        for item in provider_results:
            period = item.get("period_ended")
            if period is None:
                continue
            values[period] = {
                "revenue": item.get("revenue"),
                "ebitda": item.get("ebitda"),
                "pat": item.get("pat"),
                "eps": item.get("eps"),
            }

        periods = sorted(values.keys(), reverse=True)
        if not periods:
            raise RuntimeError(f"No valid NSE periods for {symbol}")

        results = []
        for index, period in enumerate(periods):
            current = values[period]
            previous_quarter = values[periods[index + 1]] if index + 1 < len(periods) else None
            previous_year = self.find_previous_year(period, values)

            revenue_yoy = self.calculate_growth(current["revenue"], previous_year.get("revenue") if previous_year else None)
            revenue_qoq = self.calculate_growth(current["revenue"], previous_quarter.get("revenue") if previous_quarter else None)
            ebitda_yoy = self.calculate_growth(current["ebitda"], previous_year.get("ebitda") if previous_year else None)
            ebitda_qoq = self.calculate_growth(current["ebitda"], previous_quarter.get("ebitda") if previous_quarter else None)
            pat_yoy = self.calculate_growth(current["pat"], previous_year.get("pat") if previous_year else None)
            pat_qoq = self.calculate_growth(current["pat"], previous_quarter.get("pat") if previous_quarter else None)
            eps_yoy = self.calculate_growth(current["eps"], previous_year.get("eps") if previous_year else None)

            existing = self.repository.get_by_period(symbol, period)

            summary_parts = []
            if revenue_yoy is not None:
                summary_parts.append(f"Revenue {revenue_yoy:+.1f}% YoY")
            if pat_yoy is not None:
                summary_parts.append(f"PAT {pat_yoy:+.1f}% YoY")
            if eps_yoy is not None:
                summary_parts.append(f"EPS {eps_yoy:+.1f}% YoY")
            summary = ", ".join(summary_parts) + "." if summary_parts else "Quarterly financial results filed with NSE."

            if existing:
                # IMPORTANT: never replace a valid stored actual with None.
                # Integrated XBRL can legitimately omit a fact for a filing.
                if current["revenue"] is not None:
                    existing.revenue = current["revenue"]
                    existing.revenue_yoy = revenue_yoy
                    existing.revenue_qoq = revenue_qoq
                if current["ebitda"] is not None:
                    existing.ebitda = current["ebitda"]
                    existing.ebitda_yoy = ebitda_yoy
                    existing.ebitda_qoq = ebitda_qoq
                if current["pat"] is not None:
                    existing.pat = current["pat"]
                    existing.pat_yoy = pat_yoy
                    existing.pat_qoq = pat_qoq
                if current["eps"] is not None:
                    existing.eps = current["eps"]
                    existing.eps_yoy = eps_yoy

                existing.summary = summary
                existing.source = "NSE"
                existing.source_url = self.nse_provider.WEBSITE_URL + "?symbol=" + symbol
                results.append(existing)
                continue

            result = self.repository.create(
                symbol=symbol,
                company_name=symbol,
                period_ended=period,
                period_type="Quarterly",
                consolidated=True,
                revenue=current["revenue"],
                revenue_yoy=revenue_yoy,
                revenue_qoq=revenue_qoq,
                ebitda=current["ebitda"],
                ebitda_yoy=ebitda_yoy,
                ebitda_qoq=ebitda_qoq,
                pat=current["pat"],
                pat_yoy=pat_yoy,
                pat_qoq=pat_qoq,
                eps=current["eps"],
                eps_yoy=eps_yoy,
                market_view=None,
                summary=summary,
                source="NSE",
                source_url=self.nse_provider.WEBSITE_URL + "?symbol=" + symbol,
                broadcast_date=datetime.now(timezone.utc),
            )
            results.append(result)

        self.db.commit()
        return results

    def sync_estimates(self, symbol: str) -> list:
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        print(f"Fetching IndianAPI estimates for {symbol}")
        consensus = self.indianapi_provider.get_historical(symbol)
        if not consensus:
            print(f"IndianAPI returned no historical consensus data for {symbol}")
            return []

        grouped = {}
        for item in consensus:
            if not item.is_historical:
                continue
            grouped.setdefault(item.period_ended, {})[item.metric] = item

        updated = []
        for period, metrics in grouped.items():
            result = self.repository.get_by_period(symbol, period)
            if result is None:
                continue

            for metric_name, prefix in (
                ("revenue", "revenue"),
                ("ebitda", "ebitda"),
                ("pat", "pat"),
                ("eps", "eps"),
            ):
                item = metrics.get(metric_name)
                if not item:
                    continue

                setattr(result, f"{prefix}_estimate", item.estimate)
                surprise = item.surprise_percent
                if surprise is None:
                    surprise = self.calculate_surprise(getattr(result, prefix), item.estimate)
                setattr(result, f"{prefix}_surprise_pct", surprise)
                setattr(result, f"{prefix}_result", self.classify_result(getattr(result, prefix), item.estimate))

            result.overall_result = self.calculate_overall_result(
                result.revenue_result,
                result.eps_result,
                result.pat_result,
                result.ebitda_result,
            )
            updated.append(result)

        self.db.commit()
        print(f"Updated {len(updated)} financial results with IndianAPI estimates")
        return updated

    def ingest(self, symbol: str, limit: int = 40) -> list:
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        self.ingest_nse(symbol, limit)
        try:
            self.sync_estimates(symbol)
        except Exception as exc:
            print(f"WARNING: IndianAPI estimate sync failed for {symbol}: {exc}")

        self.db.expire_all()
        return self.repository.get_recent(symbol=symbol, limit=limit)
