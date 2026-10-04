from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult
from app.models.stock import Stock
from app.schemas.screener import ScreenerFilters, ScreenerResult
from app.services.market_service import get_market_service


class StockScreenerService:
    """Rank the stocks already known to StockSage using available fundamentals.

    The score intentionally uses only values we actually have in the database or
    market quote service. Missing data is never invented and reduces the maximum
    score available to a stock.

    Score weights:
        Growth      35%  (revenue YoY + PAT YoY)
        Quality     25%  (positive PAT + EBITDA and consistency)
        Valuation   20%  (trailing PE calculated from four quarterly EPS values)
        Momentum    20%  (current daily price change as a lightweight signal)

    This is a screening/ranking model, not an investment guarantee.
    """

    def __init__(self, db: Session):
        self.db = db
        self.market = get_market_service()

    @staticmethod
    def _float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _positive_growth(value: float | None) -> float:
        if value is None:
            return 0.0
        return max(0.0, min(100.0, value * 2.0))

    @staticmethod
    def _valuation_score(pe: float | None) -> float:
        if pe is None or pe <= 0:
            return 0.0
        if pe <= 15:
            return 100.0
        if pe <= 20:
            return 90.0
        if pe <= 25:
            return 80.0
        if pe <= 30:
            return 65.0
        if pe <= 40:
            return 45.0
        if pe <= 60:
            return 25.0
        return 10.0

    @staticmethod
    def _momentum_score(change_percent: float | None) -> float:
        if change_percent is None:
            return 0.0
        # Avoid rewarding extreme one-day moves too aggressively.
        return max(0.0, min(100.0, 50.0 + change_percent * 10.0))

    def _latest_results(self, symbols: list[str]) -> dict[str, list[FinancialResult]]:
        rows = self.db.execute(
            select(FinancialResult)
            .where(FinancialResult.symbol.in_(symbols))
            .order_by(FinancialResult.symbol, FinancialResult.period_ended.desc())
        ).scalars().all()

        grouped: dict[str, list[FinancialResult]] = defaultdict(list)
        for row in rows:
            if len(grouped[row.symbol]) < 4:
                grouped[row.symbol].append(row)
        return grouped

    def _trailing_eps(self, rows: list[FinancialResult]) -> float | None:
        eps_values = [self._float(row.eps) for row in rows[:4]]
        eps_values = [value for value in eps_values if value is not None]
        if len(eps_values) < 4:
            return None
        return sum(eps_values)

    def screen(self, filters: ScreenerFilters) -> tuple[int, list[ScreenerResult]]:
        stocks = self.db.execute(
            select(Stock)
            .order_by(Stock.symbol)
            .limit(filters.universe_limit)
        ).scalars().all()

        universe_count = len(stocks)
        if not stocks:
            return 0, []

        symbols = [stock.symbol.upper() for stock in stocks]
        grouped = self._latest_results(symbols)
        candidates: list[ScreenerResult] = []

        for stock in stocks:
            symbol = stock.symbol.upper()
            rows = grouped.get(symbol, [])
            if not rows:
                continue

            latest = rows[0]
            revenue_growth = self._float(latest.revenue_yoy)
            profit_growth = self._float(latest.pat_yoy)
            eps_growth = self._float(latest.eps_yoy)
            ebitda_growth = self._float(latest.ebitda_yoy)

            if revenue_growth is None or revenue_growth < filters.min_revenue_growth:
                continue
            if profit_growth is None or profit_growth < filters.min_profit_growth:
                continue

            trailing_eps = self._trailing_eps(rows)
            price = None
            change_percent = None

            try:
                quote = self.market.get_quote(symbol)
                price = self._float(quote.price)
                change_percent = self._float(quote.change_percent)
            except Exception:
                # A temporary quote failure must not crash the complete screener.
                pass

            pe = None
            if price is not None and trailing_eps is not None and trailing_eps > 0:
                pe = price / trailing_eps

            if pe is not None and pe > filters.max_pe:
                continue

            growth_score = (
                self._positive_growth(revenue_growth) * 0.5
                + self._positive_growth(profit_growth) * 0.5
            )

            quality_components = [
                100.0 if latest.pat is not None and latest.pat > 0 else 0.0,
                100.0 if latest.ebitda is not None and latest.ebitda > 0 else 0.0,
                100.0 if ebitda_growth is not None and ebitda_growth > 0 else 0.0,
            ]
            quality_score = sum(quality_components) / len(quality_components)

            valuation_score = self._valuation_score(pe)
            momentum_score = self._momentum_score(change_percent)

            available_weights = 0.0
            weighted_score = 0.0
            weighted_score += growth_score * 0.35
            available_weights += 0.35
            weighted_score += quality_score * 0.25
            available_weights += 0.25

            if pe is not None:
                weighted_score += valuation_score * 0.20
                available_weights += 0.20
            if change_percent is not None:
                weighted_score += momentum_score * 0.20
                available_weights += 0.20

            score = weighted_score / available_weights * 100.0 / 100.0

            if score < filters.min_score:
                continue

            if score >= 80:
                verdict = "STRONG BUY CANDIDATE"
            elif score >= 70:
                verdict = "BUY CANDIDATE"
            elif score >= 60:
                verdict = "WATCH"
            else:
                verdict = "AVOID"

            candidates.append(
                ScreenerResult(
                    rank=0,
                    symbol=symbol,
                    company_name=stock.company_name,
                    sector=stock.sector,
                    score=round(score, 2),
                    verdict=verdict,
                    price=price,
                    pe=round(pe, 2) if pe is not None else None,
                    revenue_growth=revenue_growth,
                    profit_growth=profit_growth,
                    eps_growth=eps_growth,
                    quality_score=round(quality_score, 2),
                    growth_score=round(growth_score, 2),
                    valuation_score=round(valuation_score, 2) if pe is not None else None,
                    momentum_score=round(momentum_score, 2) if change_percent is not None else None,
                )
            )

        candidates.sort(key=lambda item: item.score, reverse=True)
        candidates = candidates[: filters.limit]

        for index, item in enumerate(candidates, start=1):
            item.rank = index

        return universe_count, candidates
