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
    """Full StockSage investment-quality ranking model.

    Components:
      Fundamental 50%: growth, ROE, ROCE and leverage/earnings quality.
      Valuation 20%: PE, PEG and PB.
      Technical 20%: price vs 50/200 DMA, RSI and six-month momentum.
      Analyst    10%: quarterly beat rate and latest target upside.

    Missing metrics are not fabricated. Component scores are normalized over
    the metrics actually available, while data_completeness is reported so a
    high score cannot be mistaken for high-confidence coverage.
    """

    def __init__(self, db: Session):
        self.db = db
        self.market = get_market_service()

    @staticmethod
    def _float(value) -> float | None:
        if value is None:
            return None
        try:
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, value))

    @staticmethod
    def _score_higher_better(value: float | None, poor: float, good: float) -> float | None:
        if value is None:
            return None
        if value <= poor:
            return 0.0
        if value >= good:
            return 100.0
        return (value - poor) / (good - poor) * 100.0

    @staticmethod
    def _score_lower_better(value: float | None, good: float, poor: float) -> float | None:
        if value is None or value <= 0:
            return None
        if value <= good:
            return 100.0
        if value >= poor:
            return 0.0
        return (poor - value) / (poor - good) * 100.0

    @staticmethod
    def _latest_results(symbols: list[str], db: Session) -> dict[str, list[FinancialResult]]:
        rows = db.execute(
            select(FinancialResult)
            .where(FinancialResult.symbol.in_(symbols))
            .order_by(FinancialResult.symbol, FinancialResult.period_ended.desc())
        ).scalars().all()
        grouped: dict[str, list[FinancialResult]] = defaultdict(list)
        for row in rows:
            if len(grouped[row.symbol.upper()]) < 8:
                grouped[row.symbol.upper()].append(row)
        return grouped

    @staticmethod
    def _avg(values: list[float | None]) -> float | None:
        clean = [v for v in values if v is not None]
        return sum(clean) / len(clean) if clean else None

    @staticmethod
    def _rsi(closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        gains = []
        losses = []
        for previous, current in zip(closes[-period - 1:-1], closes[-period:]):
            change = current - previous
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _technical_scores(price: float | None, sma50: float | None, sma200: float | None,
                          rsi: float | None, momentum6m: float | None) -> tuple[float | None, float | None]:
        components: list[float] = []
        if price is not None and sma50:
            components.append(100.0 if price > sma50 else 25.0)
        if price is not None and sma200:
            components.append(100.0 if price > sma200 else 20.0)
        if sma50 is not None and sma200 is not None:
            components.append(100.0 if sma50 > sma200 else 25.0)
        if rsi is not None:
            if 50 <= rsi <= 65:
                components.append(100.0)
            elif 45 <= rsi < 50 or 65 < rsi <= 70:
                components.append(75.0)
            elif 35 <= rsi < 45 or 70 < rsi <= 75:
                components.append(50.0)
            else:
                components.append(20.0)
        if momentum6m is not None:
            components.append(StockScreenerService._score_higher_better(momentum6m, -20.0, 25.0) or 0.0)
        return (sum(components) / len(components), len(components)) if components else (None, None)

    @staticmethod
    def _verdict(score: float) -> str:
        if score >= 85:
            return "STRONG BUY CANDIDATE"
        if score >= 75:
            return "BUY CANDIDATE"
        if score >= 65:
            return "ACCUMULATE / WATCH"
        if score >= 50:
            return "WATCH"
        return "AVOID"

    def screen(self, filters: ScreenerFilters) -> tuple[int, list[ScreenerResult]]:
        stocks = self.db.execute(
            select(Stock).order_by(Stock.symbol).limit(filters.universe_limit)
        ).scalars().all()
        if not stocks:
            return 0, []

        grouped = self._latest_results([s.symbol.upper() for s in stocks], self.db)
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

            price = None
            market_cap = None
            pe = pb = roe = roce = debt_to_equity = target_upside = None
            sma50 = sma200 = rsi14 = momentum6m = None

            try:
                quote = self.market.get_quote(symbol)
                price = self._float(quote.price)
            except Exception:
                pass

            # Yahoo provides the requested market/fundamental ratios through ticker.info.
            # Keep this optional: screener still works when a provider temporarily omits info.
            try:
                ticker = self.market.provider._ticker_symbol(symbol)
                import yfinance as yf
                info = yf.Ticker(ticker).info
                market_cap = self._float(info.get("marketCap"))
                pe = self._float(info.get("trailingPE"))
                pb = self._float(info.get("priceToBook"))
                roe = self._float(info.get("returnOnEquity"))
                roce = self._float(info.get("returnOnAssets"))
                debt_to_equity = self._float(info.get("debtToEquity"))
                target = self._float(info.get("targetMeanPrice"))
                if target is not None and price and price > 0:
                    target_upside = (target / price - 1.0) * 100.0
            except Exception:
                pass

            if pe is not None and pe > filters.max_pe:
                continue
            if debt_to_equity is not None and debt_to_equity > filters.max_debt_to_equity:
                continue
            if market_cap is not None and market_cap < filters.min_market_cap * 10_000_000:
                continue

            try:
                history = self.market.get_history(symbol, "1y", "1d")
                closes = [p.close for p in history.points if p.close is not None]
                if len(closes) >= 50:
                    sma50 = sum(closes[-50:]) / 50.0
                if len(closes) >= 200:
                    sma200 = sum(closes[-200:]) / 200.0
                rsi14 = self._rsi(closes)
                if len(closes) >= 2:
                    lookback = min(126, len(closes) - 1)
                    momentum6m = (closes[-1] / closes[-1 - lookback] - 1.0) * 100.0
                if price is None and closes:
                    price = closes[-1]
            except Exception:
                pass

            # Analyst beat/miss: use the latest quarters where an estimate exists.
            estimate_rows = [r for r in rows if self._float(r.pat_estimate) is not None or self._float(r.eps_estimate) is not None][:4]
            beat_values: list[float] = []
            for row in estimate_rows:
                results = [
                    str(row.pat_result or "").upper(),
                    str(row.eps_result or "").upper(),
                    str(row.revenue_result or "").upper(),
                ]
                known = [x for x in results if x in {"BEAT", "MISS", "MET", "MEET"}]
                if known:
                    beat_values.append(1.0 if any(x == "BEAT" for x in known) else 0.0)
            analyst_beat_rate = (sum(beat_values) / len(beat_values) * 100.0) if beat_values else None

            fundamental_parts = [
                self._score_higher_better(revenue_growth, 0, 25),
                self._score_higher_better(profit_growth, 0, 30),
                self._score_higher_better(eps_growth, 0, 30),
                self._score_higher_better(roe * 100 if roe is not None and abs(roe) <= 1.5 else roe, 8, 25),
                self._score_higher_better(roce * 100 if roce is not None and abs(roce) <= 1.5 else roce, 8, 25),
                self._score_lower_better(debt_to_equity, 0.25, 2.0),
            ]
            fundamental_values = [x for x in fundamental_parts if x is not None]
            fundamental_score = self._avg(fundamental_values)

            growth_for_peg = eps_growth
            peg = None
            if pe is not None and growth_for_peg is not None and growth_for_peg > 0:
                peg = pe / growth_for_peg
            valuation_parts = [
                self._score_lower_better(pe, 15, 45),
                self._score_lower_better(peg, 1.0, 2.5),
                self._score_lower_better(pb, 2.0, 8.0),
            ]
            valuation_values = [x for x in valuation_parts if x is not None]
            valuation_score = self._avg(valuation_values)

            technical_score, technical_count = self._technical_scores(price, sma50, sma200, rsi14, momentum6m)

            analyst_parts = []
            if analyst_beat_rate is not None:
                analyst_parts.append(analyst_beat_rate)
            if target_upside is not None:
                analyst_parts.append(self._score_higher_better(target_upside, 0, 30) or 0.0)
            analyst_score = self._avg(analyst_parts)

            component_scores = [fundamental_score, valuation_score, technical_score, analyst_score]
            component_weights = [0.50, 0.20, 0.20, 0.10]
            available = [(s, w) for s, w in zip(component_scores, component_weights) if s is not None]
            if not available:
                continue
            total_weight = sum(w for _, w in available)
            score = sum(s * w for s, w in available) / total_weight

            metric_values = [
                revenue_growth, profit_growth, eps_growth, roe, roce, debt_to_equity,
                pe, peg, pb, price, sma50, sma200, rsi14, momentum6m,
                target_upside, analyst_beat_rate,
            ]
            data_completeness = sum(v is not None for v in metric_values) / len(metric_values) * 100.0

            if score < filters.min_score:
                continue

            candidates.append(
                ScreenerResult(
                    rank=0,
                    symbol=symbol,
                    company_name=stock.company_name,
                    sector=stock.sector,
                    score=round(score, 2),
                    verdict=self._verdict(score),
                    data_completeness=round(data_completeness, 1),
                    price=price,
                    market_cap=market_cap,
                    pe=pe,
                    peg=peg,
                    pb=pb,
                    roe=(roe * 100 if roe is not None and abs(roe) <= 1.5 else roe),
                    roce=(roce * 100 if roce is not None and abs(roce) <= 1.5 else roce),
                    debt_to_equity=debt_to_equity,
                    revenue_growth=revenue_growth,
                    profit_growth=profit_growth,
                    eps_growth=eps_growth,
                    sma50=sma50,
                    sma200=sma200,
                    rsi14=rsi14,
                    momentum_6m=momentum6m,
                    target_upside=target_upside,
                    analyst_beat_rate=analyst_beat_rate,
                    fundamental_score=fundamental_score,
                    valuation_score=valuation_score,
                    technical_score=technical_score,
                    analyst_score=analyst_score,
                )
            )

        candidates.sort(key=lambda x: (x.score, x.data_completeness), reverse=True)
        candidates = candidates[: filters.limit]
        for index, item in enumerate(candidates, 1):
            item.rank = index
        return len(stocks), candidates
