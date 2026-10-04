from __future__ import annotations

from collections import defaultdict
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_result import FinancialResult
from app.models.stock import Stock
from app.schemas.screener import ScreenerFilters, ScreenerResult
from app.services.market_service import get_market_service


class StockScreenerService:
    """Full StockSage ranking model: fundamentals, valuation, technicals and analysts."""

    def __init__(self, db: Session):
        self.db = db
        self.market = get_market_service()

    @staticmethod
    def _float(value) -> float | None:
        if value is None:
            return None
        try:
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
        changes = [b - a for a, b in zip(closes[-period - 1:-1], closes[-period:])]
        gains = [max(c, 0.0) for c in changes]
        losses = [max(-c, 0.0) for c in changes]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - 100.0 / (1.0 + rs)

    @staticmethod
    def _roce_from_yfinance(info: dict) -> float | None:
        for key in ("returnOnCapitalEmployed", "returnOnCapital"):
            value = StockScreenerService._float(info.get(key))
            if value is not None:
                return value * 100.0 if abs(value) <= 1.5 else value

        ebitda = StockScreenerService._float(info.get("ebitda"))
        depreciation = StockScreenerService._float(info.get("depreciation"))
        assets = StockScreenerService._float(info.get("totalAssets"))
        current_liabilities = StockScreenerService._float(info.get("totalCurrentLiabilities"))
        if ebitda is not None and assets is not None and current_liabilities is not None:
            ebit = ebitda - depreciation if depreciation is not None else ebitda
            capital_employed = assets - current_liabilities
            if capital_employed > 0:
                return ebit / capital_employed * 100.0
        return None

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

    def screen(self, filters: ScreenerFilters) -> tuple[int, list[ScreenerResult]]:
        stocks = self.db.execute(select(Stock).order_by(Stock.symbol).limit(filters.universe_limit)).scalars().all()
        if not stocks:
            return 0, []

        grouped = self._latest_results(self.db, [s.symbol.upper() for s in stocks])
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
            if revenue_growth is None or revenue_growth < filters.min_revenue_growth:
                continue
            if profit_growth is None or profit_growth < filters.min_profit_growth:
                continue

            price = market_cap = pe = pb = roe = roce = debt_to_equity = target_upside = None
            try:
                quote = self.market.get_quote(symbol)
                price = self._float(quote.price)
            except Exception:
                pass

            try:
                import yfinance as yf
                ticker = yf.Ticker(self.market.provider._ticker_symbol(symbol))
                info = ticker.info
                market_cap = self._float(info.get("marketCap"))
                pe = self._float(info.get("trailingPE"))
                pb = self._float(info.get("priceToBook"))
                roe_raw = self._float(info.get("returnOnEquity"))
                roe = roe_raw * 100.0 if roe_raw is not None and abs(roe_raw) <= 1.5 else roe_raw
                roce = self._roce_from_yfinance(info)
                debt_to_equity = self._float(info.get("debtToEquity"))
                target = self._float(info.get("targetMeanPrice"))
                if target is not None and price and price > 0:
                    target_upside = (target / price - 1.0) * 100.0
            except Exception:
                pass

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
                closes = [p.close for p in history.points if p.close is not None]
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

            estimate_rows = [r for r in rows if any(self._float(x) is not None for x in (r.revenue_estimate, r.pat_estimate, r.eps_estimate))][:4]
            beat_rate = None
            if estimate_rows:
                outcomes = []
                for row in estimate_rows:
                    results = [str(x or "").upper() for x in (row.revenue_result, row.pat_result, row.eps_result)]
                    known = [x for x in results if x in {"BEAT", "MISS", "MEET", "MET"}]
                    if known:
                        outcomes.append(1.0 if "BEAT" in known else 0.0)
                if outcomes:
                    beat_rate = sum(outcomes) / len(outcomes) * 100.0

            peg = pe / eps_growth if pe is not None and eps_growth is not None and eps_growth > 0 else None

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
                technical_parts.append(100.0 if 50 <= rsi14 <= 65 else 75.0 if 45 <= rsi14 < 50 or 65 < rsi14 <= 70 else 50.0 if 35 <= rsi14 < 45 or 70 < rsi14 <= 75 else 20.0)
            if momentum6m is not None:
                technical_parts.append(self._score_higher(momentum6m, -20, 25) or 0.0)
            technical_score = self._average(technical_parts)

            analyst_score = self._average([beat_rate, self._score_higher(target_upside, 0, 30)])

            components = [fundamental_score, valuation_score, technical_score, analyst_score]
            weights = [0.50, 0.20, 0.20, 0.10]
            available = [(score, weight) for score, weight in zip(components, weights) if score is not None]
            if not available:
                continue
            total_weight = sum(weight for _, weight in available)
            score = sum(component * weight for component, weight in available) / total_weight

            metric_values = [revenue_growth, profit_growth, eps_growth, roe, roce, debt_to_equity, pe, peg, pb, price, sma50, sma200, rsi14, momentum6m, target_upside, beat_rate]
            completeness = sum(value is not None for value in metric_values) / len(metric_values) * 100.0
            if score < filters.min_score:
                continue

            candidates.append(ScreenerResult(
                rank=0,
                symbol=symbol,
                company_name=stock.company_name,
                sector=stock.sector,
                score=round(score, 2),
                verdict=("STRONG BUY CANDIDATE" if score >= 85 else "BUY CANDIDATE" if score >= 75 else "ACCUMULATE / WATCH" if score >= 65 else "WATCH" if score >= 50 else "AVOID"),
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
            ))

        candidates.sort(key=lambda item: (item.score, item.data_completeness), reverse=True)
        candidates = candidates[:filters.limit]
        for index, item in enumerate(candidates, 1):
            item.rank = index
        return len(stocks), candidates
