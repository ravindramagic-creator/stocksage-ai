from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.market_snapshot_service import MarketSnapshotService

logger = logging.getLogger("stocksage.market_snapshot_worker")

BATCH_SIZE = 50
REFRESH_INTERVAL_SECONDS = 60


async def run_market_snapshot_cycle() -> int:
    db = SessionLocal()
    try:
        count = MarketSnapshotService(db, stale_minutes=15).refresh_stale(limit=BATCH_SIZE)
        logger.info("Incremental market snapshot refresh: %d symbols", count)
        return count
    except Exception:
        logger.exception("Incremental market snapshot refresh failed")
        return 0
    finally:
        db.close()


async def market_snapshot_worker() -> None:
    logger.info("Incremental market snapshot worker started")
    while True:
        await run_market_snapshot_cycle()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
