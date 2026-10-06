from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from app.schemas.market_summary import MarketSummaryResponse
from app.services.market_cache import market_cache
from app.services.market_regime_service import MarketRegimeService
from app.services.market_service import get_market_service


class MarketSummaryService:
    """Build a concise current-day Indian market dashboard summary."""

    CACHE_KEY = "dashboard:market-summary"
    CACHE_TTL = 60

    SYMBOLS = {
        "NIFTY50": "^NSEI",
        "BANK NIFTY": "^NSEBANK",
        "NIFTY MIDCAP": "^NSEMDCP50",
        "NIFTY SMALLCAP": "^CNXSC",
        "INDIA VIX": "^INDIAVIX",
        "BRENT CRUDE": "BZ=F",
        "USD/INR": "INR=X",
    }

    def __init__(self, db):
        self.db = db
        self.market = get_market_service()

    def _get_quote(self, name: str, symbol: str):
        try:
            quote = self.market.get_quote(symbol)
            if quote is not None:
                quote.symbol = name
            return quote
        except Exception:
            return None

    def get(self) -> MarketSummaryResponse:
        cached = market_cache.get(self.CACHE_KEY)
        if cached is not None:
            return MarketSummaryResponse.model_validate(
                cached.model_dump()
                if hasattr(cached, "model_dump")
                else cached
            )

        quotes = {}

        with ThreadPoolExecutor(
            max_workers=len(self.SYMBOLS),
            thread_name_prefix="market-summary",
        ) as executor:
            futures = {
                executor.submit(
                    self._get_quote,
                    name,
                    symbol,
                ): name
                for name, symbol in self.SYMBOLS.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    quote = future.result()
                    if quote is not None:
                        quotes[name] = quote
                except Exception:
                    continue

        regime = MarketRegimeService(self.db).get()

        nifty = quotes.get("NIFTY50")
        bank = quotes.get("BANK NIFTY")
        midcap = quotes.get("NIFTY MIDCAP")
        smallcap = quotes.get("NIFTY SMALLCAP")
        vix = quotes.get("INDIA VIX")
        brent = quotes.get("BRENT CRUDE")
        usd_inr = quotes.get("USD/INR")

        index_names = {
            "NIFTY50",
            "BANK NIFTY",
            "NIFTY MIDCAP",
            "NIFTY SMALLCAP",
        }

        positive = [
            name
            for name, quote in quotes.items()
            if name in index_names
            and quote.change_percent is not None
            and quote.change_percent > 0
        ]

        negative = [
            name
            for name, quote in quotes.items()
            if name in index_names
            and quote.change_percent is not None
            and quote.change_percent < 0
        ]

        if regime.regime in {"BULL MARKET", "BULLISH"}:
            headline = "Indian equities are showing a bullish tone."
        elif regime.regime in {"BEAR MARKET", "BEARISH"}:
            headline = "Indian equities are under pressure today."
        else:
            headline = "Indian equities are showing a mixed or transitional trend."

        key_points: list[str] = []

        if nifty is not None and nifty.change_percent is not None:
            direction = "up" if nifty.change_percent >= 0 else "down"
            if nifty.price is not None:
                key_points.append(
                    f"Nifty is {direction} "
                    f"{abs(nifty.change_percent):.2f}% at "
                    f"{nifty.price:,.2f}."
                )
            else:
                key_points.append(
                    f"Nifty is {direction} "
                    f"{abs(nifty.change_percent):.2f}%."
                )

        if bank is not None and bank.change_percent is not None:
            key_points.append(
                f"Bank Nifty is "
                f"{'positive' if bank.change_percent >= 0 else 'weak'} "
                f"at {bank.change_percent:+.2f}%."
            )

        if regime.breadth_above_50dma_pct is not None:
            key_points.append(
                f"{regime.breadth_above_50dma_pct:.0f}% of tracked stocks "
                "are above their 50-DMA."
            )

        if vix is not None and vix.price is not None:
            key_points.append(
                f"India VIX is {vix.price:.2f}, "
                f"{'indicating elevated risk' if vix.price > 18 else 'remaining relatively contained'}."
            )

        if brent is not None and brent.price is not None:
            key_points.append(
                f"Brent crude is \${brent.price:,.2f}/bbl."
            )

        if usd_inr is not None and usd_inr.price is not None:
            key_points.append(
                f"USD/INR is {usd_inr.price:.2f}."
            )

        if regime.regime in {"BULL MARKET", "BULLISH"}:
            investor_takeaway = (
                "Prefer quality stocks with positive earnings growth, "
                "reasonable valuation and confirmed technical momentum."
            )
        elif regime.regime in {"BEAR MARKET", "BEARISH"}:
            investor_takeaway = (
                "Prefer selective entries, smaller position sizes and "
                "wait for stronger technical confirmation before chasing rallies."
            )
        else:
            investor_takeaway = (
                "Use staged buying and focus on stocks where fundamentals "
                "and technical momentum agree."
            )

        response = MarketSummaryResponse(
            as_of=datetime.now(timezone.utc),
            headline=headline,
            regime=regime.regime,
            regime_score=regime.score,
            nifty=nifty.price if nifty else None,
            nifty_change_percent=nifty.change_percent if nifty else None,
            bank_nifty=bank.price if bank else None,
            bank_nifty_change_percent=bank.change_percent if bank else None,
            midcap=midcap.price if midcap else None,
            midcap_change_percent=midcap.change_percent if midcap else None,
            smallcap=smallcap.price if smallcap else None,
            smallcap_change_percent=smallcap.change_percent if smallcap else None,
            india_vix=vix.price if vix else None,
            india_vix_change_percent=vix.change_percent if vix else None,
            brent=brent.price if brent else None,
            brent_change_percent=brent.change_percent if brent else None,
            usd_inr=usd_inr.price if usd_inr else None,
            usd_inr_change_percent=usd_inr.change_percent if usd_inr else None,
            breadth_above_50dma_pct=regime.breadth_above_50dma_pct,
            positive_indices=positive,
            negative_indices=negative,
            key_points=key_points[:6],
            investor_takeaway=investor_takeaway,
        )

        market_cache.set(
            self.CACHE_KEY,
            response,
            self.CACHE_TTL,
        )

        return response
