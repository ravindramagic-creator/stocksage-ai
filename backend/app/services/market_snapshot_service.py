from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_snapshot import MarketSnapshot
from app.models.stock import Stock
from app.services.market_service import get_market_service


class MarketSnapshotService:
    """Refresh only stale market snapshots instead of refetching every symbol."""

    def __init__(self, db: Session, stale_minutes: int = 15):
        self.db = db
        self.stale_seconds = stale_minutes * 60
        self.market = get_market_service()

    def _is_stale(self, row: MarketSnapshot | None, now: datetime) -> bool:
        if row is None or row.updated_at is None:
            return True
        updated = row.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        return (now - updated).total_seconds() >= self.stale_seconds

    def refresh_stale(self, limit: int = 100) -> int:
        now = datetime.now(timezone.utc)
        stocks = self.db.execute(
            select(Stock)
            .where(Stock.exchange == "NSE")
            .order_by(Stock.symbol)
        ).scalars().all()

        existing = {
            row.symbol: row
            for row in self.db.execute(select(MarketSnapshot)).scalars().all()
        }

        refreshed = 0
        for stock in stocks:
            if refreshed >= limit:
                break
            row = existing.get(stock.symbol)
            if not self._is_stale(row, now):
                continue

            if row is None:
                row = MarketSnapshot(symbol=stock.symbol)
                self.db.add(row)

            try:
                quote = self.market.get_quote(stock.symbol)
                if quote is None:
                    row.status = "unavailable"
                    row.error = "No quote available from configured providers"
                else:
                    row.price = quote.price
                    row.updated_at = now
                    row.status = "ok"
                    row.error = None
                refreshed += 1
            except Exception as exc:
                row.status = "error"
                row.error = str(exc)[:1000]
                row.updated_at = now
                refreshed += 1

        self.db.commit()
        return refreshed
