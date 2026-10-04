from __future__ import annotations

from collections import defaultdict
import math

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult
from app.models.stock import Stock
from app.schemas.screener import ScreenerFilters, ScreenerResult
from app.services.market_service import get_market_service


class StockScreenerService:
    """Rank the NSE universe using fundamental, valuation, technical and analyst signals."""

    def __init__(self, db: Session):
        self.db = db
        self.market = get_market_service()

    @staticmethod
    def _float(value) -> float | None:
        try:
            if value is None:
                return None
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None

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
    def _rsi(closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        changes = [b - a for a, b in zip(closes[-period - 1 :], closes[-period:])]
        gains = [max(change, 0.0) for change in changes]
        losses = [max(-change, 0.0) for change in changes]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _normalise_percent(value: float | None) -> float | None:
        if value is None:
            return None
        # yfinance returns returnOnEquity as a fraction, while some leverage
        # fields such as debtToEquity are commonly returned as percentages.
        return value * 100.0 if abs(value) <= 1.5 else value

    @staticmethod
    def _normalise_debt_to_equity(value: float | None) -> float | None:
        if value is None:
            return None
        # yfinance commonly exposes 48.5 for 48.5%; StockSage scores D/E as a ratio.
        return value / 100.0 if abs(value) > 10.0 else value

    @classmethod
    def _roce(cls, info: dict) -> float | None:
        for key in ("returnOnCapitalEmployed", "returnOnCapital"):
            value = cls._float(info.get(key))
            if value is not None:
                return cls._normalise_percent(value)

        ebitda = cls._float(info.get("ebitda"))
        depreciation = cls._float(info.get("depreciation"))
        assets = cls._float(info.get("totalAssets"))
        current_liabilities = cls._float(info.get("totalCurrentLiabilities"))
        if ebitda is None or assets is None or current_liabilities is None:
            return None

        ebit = ebitda - depreciation if depreciation is not None else ebitda
        capital_employed = assets - current_liabilities
        if capital_employed <= 0:
            return None
        return (ebit / capital_employed) * 100.0

    @staticmethod
    def _latest_results(db: Session, symbols: list[str]) -> dict[str, list[FinancialResult]]:
        rows = db.execute(
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

    def _fundamentals(self, symbol: str, price: float | None) -> dict[str, float | None]:
        values = {
            "market_cap": None,
            "pe": None,
            "pb": None,
            "roe": None,
            "roce": None,
            "debt_to_equity": None,
            "revenue_growth": None,
            "profit_growth": None,
            "eps_growth": None,
            "target_upside": None,
        }

        try:
            ticker = yf.Ticker(self.market.provider._ticker_symbol(symbol))
            info = ticker.info or {}

            values["market_cap"] = self._float(info.get("marketCap"))
            values["pe"] = self._float(info.get("trailingPE"))
            values["pb"] = self._float(info.get("priceToBook"))
            values["roe"] = self._normalise_percent(self._float(info.get("returnOnEquity")))
            values["roce"] = self._roce(info)
            values["debt_to_equity"] = self._normalise_debt_to_equity(
                self._float(info.get("debtToEquity"))
            )

            # Fallback growth fields make the newly synchronized NSE universe
            # screenable even before StockSage has ingested its quarterly filing.
            values["revenue_growth"] = self._normalise_percent(
                self._float(info.get("revenueGrowth"))
            )
            values["profit_growth"] = self._normalise_percent(
                self._float(
                    info.get("earningsGrowth")
                    if info.get("earningsGrowth") is not None
                    else info.get("earningsQuarterlyGrowth")
                )
            )
            values["eps_growth"] = values["profit_growth"]

            target = self._float(info.get("targetMeanPrice"))
            if target is not None and price and price > 0:
                values["target_upside"] = (target / price - 1.0) * 100.0

        except Exception:
            # One bad ticker must not prevent the full NSE universe from being screened.
            pass

        return values

    def screen(self, filters: ScreenerFilters) -> tuple[int, list[ScreenerResult]]:
        stocks = self.db.execute(
            select(Stock)
            .where(Stock.exchange == "NSE")
            .order_by(Stock.symbol)
            .limit(filters.universe_limit)
        ).scalars().all()

        if not stocks:
            return 0, []

        symbols = [stock.symbol.upper() for stock in stocks]
        grouped = self._latest_results(self.db, symbols)
        candidates: list[ScreenerResult] = []

        for stock in stocks:
            symbol = stock.symbol.upper()
            rows = grouped.get(symbol, [])
            latest = rows[0] if rows else None

            price: float | None = None
            try:
                price = self._float(self.market.get_quote(symbol).price)
            except Exception:
                pass

            fundamentals = self._fundamentals(symbol, price)
            revenue_growth = fundamentals["revenue_growth"]
            profit_growth = fundamentals["profit_growth"]
            eps_growth = fundamentals["eps_growth"]

            # Prefer StockSage's verified quarterly filing values whenever available.
            if latest is not None:
                revenue_growth = self._float(latest.revenue_yoy) or revenue_growth
                profit_growth = self._float(latest.pat_yoy) or profit_growth
                eps_growth = self._float(latest.eps_yoy) or eps_growth

            market_cap = fundamentals["market_cap"]
            pe = fundamentals["pe"]
            pb = fundamentals["pb"]
            roe = fundamentals["roe"]
            roce = fundamentals["roce"]
            debt_to_equity = fundamentals["debt_to_equity"]
            target_upside = fundamentals["target_upside"]

            # Hard filters are applied only when the metric exists. Missing data is
            # penalised through completeness rather than silently eliminating a stock.
            if revenue_growth is None or revenue_growth < filters.min_revenue_growth:
                continue
            if profit_growth is None or profit_growth < filters.min_profit_growth:
                continue
            if roe is not None and roe < filters.min_roe:
                continue
            if pe is not None and pe > filters.max_pe:
                continue
            if debt_to_equity is not None and debt_to_equity > filters.max_debt_to_equity:
                continue
            if market_cap is not None and market_cap < filters.min_market_cap * 10_000_000:
                continue

            sma50 = sma200 = rsi14 = momentum6m = None
            try:
                history = self.market.get_history(symbol, "1y", "1d")
                closes = [point.close for point in history.points if point.close is not None]
                if price is None and closes:
                    price = closes[-1]
                if len(closes) >= 50:
                    sma50 = sum(closes[-50:]) / 50.0
                if len(closes) >= 200:
                    sma200 = sum(closes[-200:]) / 200.0
                rsi14 = self._rsi(closes)
                if len(closes) >= 2:
                    lookback = min(126, len(closes) - 1)
                    momentum6m = (closes[-1] / closes[-1 - lookback] - 1.0) * 100.0
            except Exception:
                pass

            beat_rate = None
            if rows:
                estimate_rows = [
                    row
                    for row in rows
                    if any(
                        self._float(value) is not None
                        for value in (row.revenue_estimate, row.pat_estimate, row.eps_estimate)
                    )
                ][:4]
                outcomes: list[float] = []
                for row in estimate_rows:
                    results = {
                        str(value or "").strip().upper()
                        for value in (row.revenue_result, row.pat_result, row.eps_result)
                    }
                    known = results.intersection({"BEAT", "MISS", "MEET", "MET"})
                    if known:
                        outcomes.append(1.0 if "BEAT" in known else 0.0)
                if outcomes:
                    beat_rate = sum(outcomes) / len(outcomes) * 100.0

            peg = (
                pe / eps_growth
                if pe is not None and eps_growth is not None and eps_growth > 0
                else None
            )

            fundamental_score = self._average([
                self._score_higher(revenue_growth, 0, 25),
                self._score_higher(profit_growth, 0, 30),
                self._score_higher(eps_growth, 0, 30),
                self._score_higher(roe, 8, 25),
                self._score_higher(roce, 8, 25),
                self._score_lower(debt_to_equity, 0.25, 2.0),
            ])

            valuation_score = self._average([
                self._score_lower(pe, 15, 45),
                self._score_lower(peg, 1.0, 2.5),
                self._score_lower(pb, 2.0, 8.0),
            ])

            technical_parts: list[float] = []
            if price is not None and sma50 is not None:
                technical_parts.append(100.0 if price > sma50 else 20.0)
            if price is not None and sma200 is not None:
                technical_parts.append(100.0 if price > sma200 else 20.0)
            if sma50 is not None and sma200 is not None:
                technical_parts.append(100.0 if sma50 > sma200 else 25.0)
            if rsi14 is not None:
                technical_parts.append(
                    100.0 if 50 <= rsi14 <= 65 else
                    75.0 if 45 <= rsi14 < 50 or 65 < rsi14 <= 70 else
                    50.0 if 35 <= rsi14 < 45 or 70 < rsi14 <= 75 else
                    20.0
                )
            if momentum6m is not None:
                technical_parts.append(self._score_higher(momentum6m, -20, 25) or 0.0)
            technical_score = self._average(technical_parts)

            analyst_score = self._average([
                beat_rate,
                self._score_higher(target_upside, 0, 30),
            ])

            components = [fundamental_score, valuation_score, technical_score, analyst_score]
            weights = [0.50, 0.20, 0.20, 0.10]
            available = [
                (component, weight)
                for component, weight in zip(components, weights)
                if component is not None
            ]
            if not available:
                continue

            total_weight = sum(weight for _, weight in available)
            score = sum(component * weight for component, weight in available) / total_weight

            metric_values = [
                revenue_growth, profit_growth, eps_growth, roe, roce,
                debt_to_equity, pe, peg, pb, price, sma50, sma200,
                rsi14, momentum6m, target_upside, beat_rate,
            ]
            completeness = sum(value is not None for value in metric_values) / len(metric_values) * 100.0

            if score < filters.min_score:
                continue

            verdict = (
                "STRONG BUY CANDIDATE" if score >= 85 else
                "BUY CANDIDATE" if score >= 75 else
                "ACCUMULATE / WATCH" if score >= 65 else
                "WATCH" if score >= 50 else
                "AVOID"
            )

            candidates.append(
                ScreenerResult(
                    rank=0,
                    symbol=symbol,
                    company_name=stock.company_name,
                    sector=stock.sector,
                    score=round(score, 2),
                    verdict=verdict,
                    data_completeness=round(completeness, 1),
                    price=price,
                    market_cap=market_cap,
                    pe=pe,
                    peg=peg,
                    pb=pb,
                    roe=roe,
                    roce=roce,
                    debt_to_equity=debt_to_equity,
                    revenue_growth=revenue_growth,
                    profit_growth=profit_growth,
                    eps_growth=eps_growth,
                    sma50=sma50,
                    sma200=sma200,
                    rsi14=rsi14,
                    momentum_6m=momentum6m,
                    target_upside=target_upside,
                    analyst_beat_rate=beat_rate,
                    fundamental_score=fundamental_score,
                    valuation_score=valuation_score,
                    technical_score=technical_score,
                    analyst_score=analyst_score,
                )
            )

        candidates.sort(key=lambda item: (item.score, item.data_completeness), reverse=True)
        candidates = candidates[:filters.limit]
        for rank, item in enumerate(candidates, 1):
            item.rank = rank

        return len(stocks), candidates
