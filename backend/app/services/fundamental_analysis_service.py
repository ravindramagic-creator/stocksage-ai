from __future__ import annotations

from math import isfinite

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult
from app.models.market_snapshot import MarketSnapshot
from app.models.stock import Stock
from app.schemas.fundamental_analysis import FundamentalAnalysisResponse
from app.services.market_snapshot_service import MarketSnapshotService


class FundamentalAnalysisService:
    """Build a fast fundamental view for an individual stock page."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _number(value) -> float | None:
        try:
            number = float(value) if value is not None else None
            return number if isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _positive_score(
        value: float | None,
        weak: float,
        strong: float,
    ) -> float | None:
        if value is None:
            return None
        if value <= weak:
            return 0.0
        if value >= strong:
            return 100.0
        return (value - weak) / (strong - weak) * 100.0

    @staticmethod
    def _valuation_score(
        value: float | None,
        good: float,
        expensive: float,
    ) -> float | None:
        if value is None or value <= 0:
            return None
        if value <= good:
            return 100.0
        if value >= expensive:
            return 0.0
        return (expensive - value) / (expensive - good) * 100.0

    @staticmethod
    def _average(
        values: list[float | None],
    ) -> float | None:
        clean = [
            value for value in values
            if value is not None
        ]
        return (
            sum(clean) / len(clean)
            if clean
            else None
        )

    def _ensure_snapshot(
        self,
        symbol: str,
    ) -> MarketSnapshot | None:
        """Populate a missing stock snapshot on first stock-page visit.

        The background worker normally fills MarketSnapshot asynchronously.
        A user can open a stock page before that worker reaches the symbol,
        however. In that case the old endpoint returned 404 and the UI showed
        'Fundamental data is not available yet'. Refresh only the requested
        symbol here so the first visit can self-heal without scanning the NSE
        universe.
        """
        snapshot = self.db.scalar(
            select(MarketSnapshot).where(
                MarketSnapshot.symbol == symbol,
            )
        )

        if snapshot is not None:
            return snapshot

        stock = self.db.scalar(
            select(Stock).where(
                Stock.symbol == symbol,
            )
        )

        if stock is None:
            return None

        service = MarketSnapshotService(
            self.db,
            stale_minutes=30,
        )

        snapshot = MarketSnapshot(
            symbol=symbol,
            status="pending",
        )
        self.db.add(snapshot)

        try:
            service._refresh_symbol(
                stock,
                snapshot,
                service._now(),
            )
            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot
        except Exception:
            self.db.rollback()
            return None

    def analyze(
        self,
        symbol: str,
    ) -> FundamentalAnalysisResponse | None:
        normalized = symbol.strip().upper()

        stock = self.db.scalar(
            select(Stock).where(
                Stock.symbol == normalized,
            )
        )

        if stock is None:
            return None

        snapshot = self._ensure_snapshot(
            normalized,
        )

        latest = self.db.execute(
            select(FinancialResult)
            .where(
                FinancialResult.symbol == normalized,
            )
            .order_by(
                FinancialResult.period_ended.desc(),
            )
            .limit(1),
        ).scalar_one_or_none()

        if snapshot is None:
            return None

        revenue_growth = self._number(
            snapshot.revenue_growth,
        )
        profit_growth = self._number(
            snapshot.profit_growth,
        )
        eps_growth = profit_growth

        if latest is not None:
            if latest.revenue_yoy is not None:
                revenue_growth = self._number(
                    latest.revenue_yoy,
                )
            if latest.pat_yoy is not None:
                profit_growth = self._number(
                    latest.pat_yoy,
                )
            if latest.eps_yoy is not None:
                eps_growth = self._number(
                    latest.eps_yoy,
                )

        roe = self._number(snapshot.roe)
        roce = self._number(snapshot.roce)
        debt_to_equity = self._number(
            snapshot.debt_to_equity,
        )
        pe = self._number(snapshot.pe)
        pb = self._number(snapshot.pb)
        target_upside = self._number(
            snapshot.target_upside,
        )
        analyst_beat_rate = self._number(
            snapshot.analyst_beat_rate,
        )

        peg = None
        if (
            pe is not None
            and eps_growth is not None
            and eps_growth > 0
        ):
            peg = pe / eps_growth

        growth_score = self._average(
            [
                self._positive_score(
                    revenue_growth,
                    0,
                    30,
                ),
                self._positive_score(
                    profit_growth,
                    0,
                    40,
                ),
                self._positive_score(
                    eps_growth,
                    0,
                    40,
                ),
            ]
        )

        profitability_score = self._average(
            [
                self._positive_score(
                    roe,
                    8,
                    25,
                ),
                self._positive_score(
                    roce,
                    8,
                    25,
                ),
            ]
        )

        valuation_score = self._average(
            [
                self._valuation_score(
                    pe,
                    18,
                    45,
                ),
                self._valuation_score(
                    peg,
                    1,
                    2.5,
                ),
                self._valuation_score(
                    pb,
                    3,
                    8,
                ),
            ]
        )

        leverage_score = None
        if debt_to_equity is not None:
            if debt_to_equity <= 0.5:
                leverage_score = 100.0
            elif debt_to_equity <= 1.5:
                leverage_score = 70.0
            elif debt_to_equity <= 2.5:
                leverage_score = 35.0
            else:
                leverage_score = 0.0

        earnings_score = self._average(
            [
                analyst_beat_rate,
                self._positive_score(
                    target_upside,
                    0,
                    30,
                ),
                (
                    100.0
                    if latest is not None
                    and latest.overall_result == "BEAT"
                    else 50.0
                    if latest is not None
                    and latest.overall_result == "MEET"
                    else 0.0
                    if latest is not None
                    and latest.overall_result == "MISS"
                    else None
                ),
            ]
        )

        components = [
            (growth_score, 0.30),
            (profitability_score, 0.25),
            (valuation_score, 0.20),
            (leverage_score, 0.15),
            (earnings_score, 0.10),
        ]

        available = [
            (score, weight)
            for score, weight in components
            if score is not None
        ]

        overall_score = None

        if available:
            total_weight = sum(
                weight
                for _, weight in available
            )
            overall_score = sum(
                score * weight
                for score, weight in available
            ) / total_weight

        metric_values = [
            revenue_growth,
            profit_growth,
            eps_growth,
            roe,
            roce,
            debt_to_equity,
            pe,
            peg,
            pb,
        ]

        completeness = (
            sum(
                value is not None
                for value in metric_values
            )
            / len(metric_values)
            * 100.0
        )

        strengths: list[str] = []
        risks: list[str] = []

        if revenue_growth is not None:
            if revenue_growth >= 15:
                strengths.append(
                    f"Revenue growth is strong at "
                    f"{revenue_growth:.1f}% YoY."
                )
            elif revenue_growth > 0:
                strengths.append(
                    f"Revenue is growing at "
                    f"{revenue_growth:.1f}% YoY."
                )

        if profit_growth is not None:
            if profit_growth >= 15:
                strengths.append(
                    f"Profit growth is strong at "
                    f"{profit_growth:.1f}% YoY."
                )
            elif profit_growth < 0:
                risks.append(
                    f"Profit is declining "
                    f"{abs(profit_growth):.1f}% YoY."
                )

        if roe is not None:
            if roe >= 15:
                strengths.append(
                    f"ROE of {roe:.1f}% indicates "
                    "good capital efficiency."
                )
            elif roe < 10:
                risks.append(
                    f"ROE is low at {roe:.1f}%."
                )

        if roce is not None:
            if roce >= 15:
                strengths.append(
                    f"ROCE of {roce:.1f}% is healthy."
                )
            elif roce < 10:
                risks.append(
                    f"ROCE is weak at {roce:.1f}%."
                )

        if debt_to_equity is not None:
            if debt_to_equity <= 1:
                strengths.append(
                    f"Debt/Equity is manageable at "
                    f"{debt_to_equity:.2f}."
                )
            elif debt_to_equity > 1.5:
                risks.append(
                    f"Debt/Equity is elevated at "
                    f"{debt_to_equity:.2f}."
                )

        if pe is not None:
            if pe <= 25:
                strengths.append(
                    f"P/E of {pe:.1f}x is relatively reasonable."
                )
            elif pe > 45:
                risks.append(
                    f"P/E of {pe:.1f}x indicates a rich valuation."
                )

        if peg is not None:
            if peg <= 2:
                strengths.append(
                    f"PEG of {peg:.2f} is reasonable relative to growth."
                )
            elif peg > 2.5:
                risks.append(
                    f"PEG of {peg:.2f} suggests the valuation is demanding."
                )

        if latest is not None:
            if latest.overall_result == "BEAT":
                strengths.append(
                    "Latest reported results beat expectations."
                )
            elif latest.overall_result == "MISS":
                risks.append(
                    "Latest reported results missed expectations."
                )

        if target_upside is not None:
            if target_upside >= 10:
                strengths.append(
                    f"Analyst target implies about "
                    f"{target_upside:.1f}% upside."
                )
            elif target_upside < 0:
                risks.append(
                    f"Analyst target implies about "
                    f"{target_upside:.1f}% downside."
                )

        if overall_score is None:
            verdict = "DATA INSUFFICIENT"
        elif overall_score >= 80:
            verdict = "STRONG"
        elif overall_score >= 65:
            verdict = "GOOD"
        elif overall_score >= 50:
            verdict = "AVERAGE"
        else:
            verdict = "WEAK"

        summary_parts: list[str] = []

        if overall_score is not None:
            summary_parts.append(
                f"Fundamental score "
                f"{overall_score:.0f}/100."
            )

        if growth_score is not None:
            summary_parts.append(
                f"Growth quality is "
                f"{growth_score:.0f}/100."
            )

        if profitability_score is not None:
            summary_parts.append(
                f"Profitability is "
                f"{profitability_score:.0f}/100."
            )

        if valuation_score is not None:
            summary_parts.append(
                f"Valuation is "
                f"{valuation_score:.0f}/100."
            )

        return FundamentalAnalysisResponse(
            symbol=normalized,
            company_name=stock.company_name,
            overall_score=(
                round(overall_score, 2)
                if overall_score is not None
                else None
            ),
            verdict=verdict,
            data_completeness=round(
                completeness,
                1,
            ),
            revenue_growth=revenue_growth,
            profit_growth=profit_growth,
            eps_growth=eps_growth,
            roe=roe,
            roce=roce,
            debt_to_equity=debt_to_equity,
            pe=pe,
            peg=peg,
            pb=pb,
            analyst_beat_rate=analyst_beat_rate,
            target_upside=target_upside,
            latest_revenue_yoy=(
                self._number(
                    latest.revenue_yoy,
                )
                if latest is not None
                else None
            ),
            latest_pat_yoy=(
                self._number(
                    latest.pat_yoy,
                )
                if latest is not None
                else None
            ),
            latest_eps_yoy=(
                self._number(
                    latest.eps_yoy,
                )
                if latest is not None
                else None
            ),
            latest_result=(
                latest.overall_result
                if latest is not None
                else None
            ),
            strengths=strengths[:6],
            risks=risks[:6],
            summary=(
                " ".join(summary_parts)
                if summary_parts
                else "Fundamental data is not yet sufficient for a reliable assessment."
            ),
        )
