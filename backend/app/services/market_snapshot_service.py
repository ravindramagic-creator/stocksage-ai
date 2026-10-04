from __future__ import annotations

from datetime import datetime, timezone
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_snapshot import MarketSnapshot
from app.models.stock import Stock
from app.services.market_data.yahoo_fundamentals_provider import YahooFundamentalsProvider
from app.services.market_service import get_market_service


class MarketSnapshotService:
    """Incrementally build the complete scoring dataset in the background."""

    def __init__(self, db: Session, stale_minutes: int = 30):
        self.db = db
        self.stale_seconds = stale_minutes * 60
        self.market = get_market_service()
        self.yahoo_fundamentals = YahooFundamentalsProvider()

    @staticmethod
    def _number(value) -> float | None:
        try:
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    @classmethod
    def _percent(cls, value) -> float | None:
        value = cls._number(value)
        if value is None:
            return None
        return value * 100 if abs(value) <= 1.5 else value

    @classmethod
    def _debt(cls, value) -> float | None:
        value = cls._number(value)
        if value is None:
            return None
        return value / 100 if abs(value) > 10 else value

    @classmethod
    def _rsi(cls, closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None
        changes = [b - a for a, b in zip(closes[-period - 1:], closes[-period:])]
        gains = [max(change, 0.0) for change in changes]
        losses = [max(-change, 0.0) for change in changes]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100.0 if avg_gain else 50.0
        return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    def _is_stale(self, row: MarketSnapshot | None, now: datetime) -> bool:
        if row is None or row.updated_at is None:
            return True
        updated = row.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return (now - updated).total_seconds() >= self.stale_seconds

    def _refresh_symbol(self, stock: Stock, row: MarketSnapshot, now: datetime) -> None:
        symbol = stock.symbol.upper()
        quote = self.market.get_quote(symbol)
        if quote is None:
            row.status = "unavailable"
            row.error = "No quote available from configured providers"
            row.updated_at = now
            return

        row.price = self._number(quote.price)
        row.status = "ok"
        row.error = None

        try:
            data = self.yahoo_fundamentals.get_snapshot_data(symbol)
            info = data.get("info", {})
            row.market_cap = self._number(info.get("marketCap"))
            row.pe = self._number(info.get("trailingPE"))
            row.pb = self._number(info.get("priceToBook"))
            row.roe = self._percent(info.get("returnOnEquity"))
            row.roce = self._percent(info.get("returnOnAssets"))
            row.debt_to_equity = self._debt(info.get("debtToEquity"))
            row.revenue_growth = self._percent(info.get("revenueGrowth"))
            row.profit_growth = self._percent(info.get("earningsGrowth"))
            target = self._number(info.get("targetMeanPrice"))
            row.target_upside = ((target / row.price) - 1) * 100 if target and row.price else None

            history = self.yahoo_fundamentals.get_history(symbol)
            closes = [self._number(v) for v in history.get("Close", []).tolist()]
            closes = [value for value in closes if value is not None]
            if len(closes) >= 50:
                row.sma50 = sum(closes[-50:]) / 50
            if len(closes) >= 200:
                row.sma200 = sum(closes[-200:]) / 200
            row.rsi14 = self._rsi(closes)
            if len(closes) >= 2:
                lookback = min(126, len(closes) - 1)
                row.momentum_6m = (closes[-1] / closes[-1 - lookback] - 1) * 100
        except Exception as exc:
            # Preserve any good values already in the snapshot. A provider
            # outage must not erase usable historical scoring data.
            row.error = f"partial snapshot: {str(exc)[:900]}"
            if "cooling down" in str(exc).lower():
                row.status = "partial"

        row.updated_at = now

    def refresh_stale(self, limit: int = 50) -> int:
        now = datetime.now(timezone.utc)
        stocks = self.db.execute(
            select(Stock).where(Stock.exchange == "NSE").order_by(Stock.symbol)
        ).scalars().all()
        existing = {
            row.symbol.upper(): row
            for row in self.db.execute(select(MarketSnapshot)).scalars().all()
        }

        refreshed = 0
        for stock in stocks:
            if refreshed >= limit:
                break
            row = existing.get(stock.symbol.upper())
            if not self._is_stale(row, now):
                continue
            if row is None:
                row = MarketSnapshot(symbol=stock.symbol.upper(), status="pending")
                self.db.add(row)
            try:
                self._refresh_symbol(stock, row, now)
            except Exception as exc:
                row.status = "error"
                row.error = str(exc)[:1000]
                row.updated_at = now
            refreshed += 1

        self.db.commit()
        return refreshed
