from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.screener_snapshot_service import ScreenerSnapshotService

logger = logging.getLogger("stocksage.screener_worker")

# The screener itself is database-only. MarketSnapshotWorker is responsible
# for upstream provider calls, so rebuilding the screener snapshot frequently
# is inexpensive and keeps rankings aligned with newly repaired fundamentals.
SCREENER_REFRESH_SECONDS = 15 * 60


async def run_screener_refresh() -> None:
    db = SessionLocal()
    try:
        count = ScreenerSnapshotService(db).refresh(universe_limit=5000)
        logger.info("Screener snapshot refreshed: %d stocks", count)
    except Exception:
        logger.exception(
            "Screener snapshot refresh failed; keeping last snapshot"
        )
    finally:
        db.close()


async def screener_worker() -> None:
    logger.info("Screener snapshot worker started")

    # Build once at startup, then refresh frequently from the persisted
    # MarketSnapshot data. No Yahoo/NSE calls happen in this worker.
    asyncio.create_task(run_screener_refresh())

    while True:
        await asyncio.sleep(SCREENER_REFRESH_SECONDS)
        await run_screener_refresh()
