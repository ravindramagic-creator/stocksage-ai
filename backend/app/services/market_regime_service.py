from __future__ import annotations

from math import isfinite

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.market_snapshot import MarketSnapshot
from app.schemas.market_regime import (
    MarketRegimeFactor,
    MarketRegimeResponse,
)
from app.services.market_cache import market_cache
from app.services.market_service import get_market_service


class MarketRegimeService:
    """Classify the Indian market using trend, momentum, volatility and breadth."""

    CACHE_KEY = "dashboard:market-regime"
    CACHE_TTL = 60

    def __init__(self, db: Session):
        self.db = db
        self.market = get_market_service()

    @staticmethod
    def _number(value) -> float | None:
        try:
            number = float(value)
            return number if isfinite(number) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _rsi(
        closes: list[float],
        period: int = 14,
    ) -> float | None:
        if len(closes) <= period:
            return None

        gains = 0.0
        losses = 0.0

        for index in range(
            len(closes) - period,
            len(closes),
        ):
            change = closes[index] - closes[index - 1]
            if change >= 0:
                gains += change
            else:
                losses -= change

        avg_gain = gains / period
        avg_loss = losses / period

        if avg_loss == 0:
            return 100.0 if avg_gain else 50.0

        return 100.0 - (
            100.0
            / (1.0 + avg_gain / avg_loss)
        )

    def _nifty_metrics(self):
        history = self.market.get_history(
            "^NSEI",
            period="1y",
            interval="1d",
        )

        closes = [
            self._number(point.close)
            for point in history.points
        ]
        closes = [
            close
            for close in closes
            if close is not None
        ]

        if not closes:
            return None

        price = closes[-1]
        sma50 = (
            sum(closes[-50:]) / 50
            if len(closes) >= 50
            else None
        )
        sma200 = (
            sum(closes[-200:]) / 200
            if len(closes) >= 200
            else None
        )
        rsi = self._rsi(closes)

        momentum_6m = None
        if len(closes) >= 2:
            lookback = min(
                126,
                len(closes) - 1,
            )
            momentum_6m = (
                closes[-1]
                / closes[-1 - lookback]
                - 1
            ) * 100

        return (
            price,
            sma50,
            sma200,
            rsi,
            momentum_6m,
        )

    def _breadth(self) -> float | None:
        total = self.db.scalar(
            select(func.count())
            .select_from(MarketSnapshot)
            .where(
                MarketSnapshot.status.in_(
                    ["ok", "partial"],
                ),
                MarketSnapshot.price.is_not(None),
                MarketSnapshot.sma50.is_not(None),
            )
        ) or 0

        above = self.db.scalar(
            select(func.count())
            .select_from(MarketSnapshot)
            .where(
                MarketSnapshot.status.in_(
                    ["ok", "partial"],
                ),
                MarketSnapshot.price.is_not(None),
                MarketSnapshot.sma50.is_not(None),
                MarketSnapshot.price
                > MarketSnapshot.sma50,
            )
        ) or 0

        if total < 20:
            return None

        return (
            above
            / total
            * 100
        )

    def get(self) -> MarketRegimeResponse:
        cached = market_cache.get(
            self.CACHE_KEY
        )
        if cached is not None:
            return MarketRegimeResponse.model_validate(
                cached.model_dump()
                if hasattr(cached, "model_dump")
                else cached
            )

        nifty = self._nifty_metrics()

        if nifty is None:
            response = MarketRegimeResponse(
                regime="DATA UNAVAILABLE",
                score=0,
                bullish_signals=0,
                bearish_signals=0,
                neutral_signals=0,
                factors=[],
                note="Nifty history is temporarily unavailable.",
            )
            market_cache.set(
                self.CACHE_KEY,
                response,
                self.CACHE_TTL,
            )
            return response

        (
            price,
            sma50,
            sma200,
            rsi,
            momentum_6m,
        ) = nifty

        vix_quote = self.market.get_quote(
            "^INDIAVIX",
        )
        vix = (
            self._number(vix_quote.price)
            if vix_quote is not None
            else None
        )

        breadth = self._breadth()

        factors: list[MarketRegimeFactor] = []
        bullish = 0
        bearish = 0
        neutral = 0

        def add(
            name: str,
            bullish_state: bool | None,
            detail: str,
        ) -> None:
            nonlocal bullish
            nonlocal bearish
            nonlocal neutral

            if bullish_state is True:
                status = "BULLISH"
                bullish += 1
            elif bullish_state is False:
                status = "BEARISH"
                bearish += 1
            else:
                status = "NEUTRAL"
                neutral += 1

            factors.append(
                MarketRegimeFactor(
                    name=name,
                    status=status,
                    detail=detail,
                )
            )

        add(
            "Nifty vs 50-DMA",
            None if sma50 is None else price > sma50,
            (
                "Price is above 50-DMA."
                if sma50 is not None and price > sma50
                else "Price is below 50-DMA."
                if sma50 is not None
                else "50-DMA unavailable."
            ),
        )

        add(
            "Nifty vs 200-DMA",
            None if sma200 is None else price > sma200,
            (
                "Price is above 200-DMA."
                if sma200 is not None and price > sma200
                else "Price is below 200-DMA."
                if sma200 is not None
                else "200-DMA unavailable."
            ),
        )

        add(
            "50-DMA vs 200-DMA",
            (
                None
                if sma50 is None or sma200 is None
                else sma50 > sma200
            ),
            (
                "50-DMA is above 200-DMA."
                if sma50 is not None
                and sma200 is not None
                and sma50 > sma200
                else "50-DMA is below 200-DMA."
                if sma50 is not None
                and sma200 is not None
                else "Moving-average structure unavailable."
            ),
        )

        add(
            "RSI-14",
            None if rsi is None else rsi >= 50,
            (
                f"RSI is {rsi:.1f}, showing positive momentum."
                if rsi is not None and rsi >= 50
                else f"RSI is {rsi:.1f}, showing weak momentum."
                if rsi is not None
                else "RSI unavailable."
            ),
        )

        add(
            "6M Momentum",
            None if momentum_6m is None else momentum_6m > 0,
            (
                f"6M momentum is +{momentum_6m:.1f}%."
                if momentum_6m is not None and momentum_6m > 0
                else f"6M momentum is {momentum_6m:.1f}%."
                if momentum_6m is not None
                else "6M momentum unavailable."
            ),
        )

        add(
            "Market Breadth",
            None if breadth is None else breadth >= 50,
            (
                f"{breadth:.0f}% of tracked stocks are above 50-DMA."
                if breadth is not None
                else "Insufficient snapshot data for breadth."
            ),
        )

        add(
            "India VIX",
            None if vix is None else vix <= 18,
            (
                f"India VIX is {vix:.2f}, supporting risk appetite."
                if vix is not None and vix <= 18
                else f"India VIX is {vix:.2f}, indicating elevated risk."
                if vix is not None
                else "India VIX unavailable."
            ),
        )

        total_signals = bullish + bearish

        if total_signals == 0:
            regime = "DATA UNAVAILABLE"
        elif bullish >= 6:
            regime = "BULL MARKET"
        elif bearish >= 5:
            regime = "BEAR MARKET"
        elif bullish > bearish + 1:
            regime = "BULLISH"
        elif bearish > bullish + 1:
            regime = "BEARISH"
        else:
            regime = "TRANSITION"

        score = round(
            (
                bullish / total_signals * 100
            )
            if total_signals
            else 0
        )

        if regime in {"BULL MARKET", "BULLISH"}:
            note = (
                "Trend and breadth favor buying quality stocks, "
                "but valuation and stock-specific risks still matter."
            )
        elif regime in {"BEAR MARKET", "BEARISH"}:
            note = (
                "Market conditions are weak. Prefer selective buying "
                "and stronger technical confirmation."
            )
        else:
            note = (
                "Signals are mixed. Prefer staged entries and wait "
                "for clearer trend confirmation."
            )

        response = MarketRegimeResponse(
            regime=regime,
            score=score,
            bullish_signals=bullish,
            bearish_signals=bearish,
            neutral_signals=neutral,
            nifty=price,
            nifty_50dma=sma50,
            nifty_200dma=sma200,
            nifty_rsi=rsi,
            nifty_momentum_6m=momentum_6m,
            india_vix=vix,
            breadth_above_50dma_pct=breadth,
            factors=factors,
            note=note,
        )

        market_cache.set(
            self.CACHE_KEY,
            response,
            self.CACHE_TTL,
        )

        return response
