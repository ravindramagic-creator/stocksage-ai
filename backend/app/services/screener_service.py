from __future__ import annotations

from collections import defaultdict
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult
from app.models.market_snapshot import MarketSnapshot
from app.models.stock import Stock
from app.schemas.screener import ScreenerFilters, ScreenerResult


class StockScreenerService:
    """Database-only scoring engine. External market providers run in workers."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _score_higher(value: float | None, poor: float, good: float) -> float | None:
        if value is None:
            return None
        if value <= poor:
            return 0.0
        if value >= good:
            return 100.0
        return (value - poor) / (good - poor) * 100.0

    @staticmethod
    def _score_lower(value: float | None, good: float, poor: float) -> float | None:
        if value is None or value <= 0:
            return None
        if value <= good:
            return 100.0
        if value >= poor:
            return 0.0
        return (poor - value) / (poor - good) * 100.0

    @staticmethod
    def _average(values: list[float | None]) -> float | None:
        clean = [v for v in values if v is not None]
        return sum(clean) / len(clean) if clean else None

    @staticmethod
    def _float(value) -> float | None:
        try:
            number = float(value) if value is not None else None
            return number if number is not None and math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

    def _latest_results(self, symbols: list[str]) -> dict[str, list[FinancialResult]]:
        rows = self.db.execute(
            select(FinancialResult)
            .where(FinancialResult.symbol.in_(symbols))
            .order_by(FinancialResult.symbol, FinancialResult.period_ended.desc())
        ).scalars().all()
        grouped: dict[str, list[FinancialResult]] = defaultdict(list)
        for row in rows:
            key = row.symbol.upper()
            if len(grouped[key]) < 8:
                grouped[key].append(row)
        return grouped

    @staticmethod
    def _beat_rate(rows: list[FinancialResult]) -> float | None:
        outcomes: list[float] = []
        for row in rows[:4]:
            values = {str(v or "").strip().upper() for v in (row.revenue_result, row.pat_result, row.eps_result)}
            if "BEAT" in values:
                outcomes.append(1.0)
            elif values.intersection({"MISS", "MEET", "MET"}):
                outcomes.append(0.0)
        return sum(outcomes) / len(outcomes) * 100.0 if outcomes else None

    def screen(self, filters: ScreenerFilters, offset: int = 0) -> tuple[int, list[ScreenerResult]]:
        # No Yahoo/NSE call is allowed on this path. MarketSnapshot is populated
        # asynchronously by the market snapshot worker.
        stocks = self.db.execute(
            select(Stock)
            .where(Stock.exchange == "NSE")
            .order_by(Stock.symbol)
            .offset(offset)
            .limit(filters.limit)
        ).scalars().all()
        if not stocks:
            return 0, []

        symbols = [stock.symbol.upper() for stock in stocks]
        snapshots = {
            row.symbol.upper(): row
            for row in self.db.execute(
                select(MarketSnapshot).where(MarketSnapshot.symbol.in_(symbols))
            ).scalars().all()
        }
        grouped = self._latest_results(symbols)
        candidates: list[ScreenerResult] = []

        for stock in stocks:
            symbol = stock.symbol.upper()
            snap = snapshots.get(symbol)
            if snap is None or snap.status != "ok":
                continue

            rows = grouped.get(symbol, [])
            latest = rows[0] if rows else None
            revenue_growth = self._float(latest.revenue_yoy) if latest and latest.revenue_yoy is not None else snap.revenue_growth
            profit_growth = self._float(latest.pat_yoy) if latest and latest.pat_yoy is not None else snap.profit_growth
            eps_growth = self._float(latest.eps_yoy) if latest and latest.eps_yoy is not None else profit_growth
            beat_rate = self._beat_rate(rows)
            beat_rate = beat_rate if beat_rate is not None else snap.analyst_beat_rate

            if revenue_growth is None or revenue_growth < filters.min_revenue_growth:
                continue
            if profit_growth is None or profit_growth < filters.min_profit_growth:
                continue
            if snap.roe is not None and snap.roe < filters.min_roe:
                continue
            if snap.pe is not None and snap.pe > filters.max_pe:
                continue
            if snap.debt_to_equity is not None and snap.debt_to_equity > filters.max_debt_to_equity:
                continue
            if snap.market_cap is not None and snap.market_cap < filters.min_market_cap * 10_000_000:
                continue

            peg = snap.pe / eps_growth if snap.pe is not None and eps_growth and eps_growth > 0 else None
            fundamental_score = self._average([
                self._score_higher(revenue_growth, 0, 25),
                self._score_higher(profit_growth, 0, 30),
                self._score_higher(eps_growth, 0, 30),
                self._score_higher(snap.roe, 8, 25),
                self._score_higher(snap.roce, 8, 25),
                self._score_lower(snap.debt_to_equity, 0.25, 2.0),
            ])
            valuation_score = self._average([
                self._score_lower(snap.pe, 15, 45),
                self._score_lower(peg, 1.0, 2.5),
                self._score_lower(snap.pb, 2.0, 8.0),
            ])

            technical_parts: list[float | None] = []
            if snap.price is not None and snap.sma50 is not None:
                technical_parts.append(100.0 if snap.price > snap.sma50 else 20.0)
            if snap.price is not None and snap.sma200 is not None:
                technical_parts.append(100.0 if snap.price > snap.sma200 else 20.0)
            if snap.sma50 is not None and snap.sma200 is not None:
                technical_parts.append(100.0 if snap.sma50 > snap.sma200 else 25.0)
            if snap.rsi14 is not None:
                technical_parts.append(100.0 if 50 <= snap.rsi14 <= 65 else 75.0 if 45 <= snap.rsi14 < 50 or 65 < snap.rsi14 <= 70 else 50.0 if 35 <= snap.rsi14 < 45 or 70 < snap.rsi14 <= 75 else 20.0)
            if snap.momentum_6m is not None:
                technical_parts.append(self._score_higher(snap.momentum_6m, -20, 25))
            technical_score = self._average(technical_parts)
            analyst_score = self._average([beat_rate, self._score_higher(snap.target_upside, 0, 30)])

            weighted = [(fundamental_score, .50), (valuation_score, .20), (technical_score, .20), (analyst_score, .10)]
            available = [(value, weight) for value, weight in weighted if value is not None]
            if not available:
                continue
            total_weight = sum(weight for _, weight in available)
            score = sum(value * weight for value, weight in available) / total_weight
            if score < filters.min_score:
                continue

            metric_values = [revenue_growth, profit_growth, eps_growth, snap.roe, snap.roce, snap.debt_to_equity, snap.pe, peg, snap.pb, snap.price, snap.sma50, snap.sma200, snap.rsi14, snap.momentum_6m, snap.target_upside, beat_rate]
            completeness = sum(value is not None for value in metric_values) / len(metric_values) * 100.0
            verdict = "STRONG BUY CANDIDATE" if score >= 85 else "BUY CANDIDATE" if score >= 75 else "ACCUMULATE / WATCH" if score >= 65 else "WATCH" if score >= 50 else "AVOID"

            candidates.append(ScreenerResult(
                rank=0, symbol=symbol, company_name=stock.company_name, sector=stock.sector,
                score=round(score, 2), verdict=verdict, data_completeness=round(completeness, 1),
                price=snap.price, market_cap=snap.market_cap, pe=snap.pe, peg=peg, pb=snap.pb,
                roe=snap.roe, roce=snap.roce, debt_to_equity=snap.debt_to_equity,
                revenue_growth=revenue_growth, profit_growth=profit_growth, eps_growth=eps_growth,
                sma50=snap.sma50, sma200=snap.sma200, rsi14=snap.rsi14, momentum_6m=snap.momentum_6m,
                target_upside=snap.target_upside, analyst_beat_rate=beat_rate,
                fundamental_score=fundamental_score, valuation_score=valuation_score,
                technical_score=technical_score, analyst_score=analyst_score,
            ))

        candidates.sort(key=lambda item: (item.score, item.data_completeness), reverse=True)
        candidates = candidates[:filters.limit]
        for rank, item in enumerate(candidates, 1):
            item.rank = rank
        return len(stocks), candidates
