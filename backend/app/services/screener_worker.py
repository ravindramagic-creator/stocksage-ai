from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.screener_snapshot_service import ScreenerSnapshotService

logger = logging.getLogger("stocksage.screener_worker")

# Full-universe calculations are expensive and upstream providers are rate
# limited. Refresh periodically in the background rather than from HTTP.
SCREENER_REFRESH_SECONDS = 6 * 60 * 60


async def run_screener_refresh() -> None:
    db = SessionLocal()
    try:
        count = ScreenerSnapshotService(db).refresh(universe_limit=5000)
        logger.info("Screener snapshot refreshed: %d stocks", count)
    except Exception:
        logger.exception("Screener snapshot refresh failed; keeping last snapshot")
    finally:
        db.close()


async def screener_worker() -> None:
    logger.info("Screener snapshot worker started")

    # Do not block FastAPI startup. The existing snapshot, if any, remains
    # available while the first expensive refresh runs.
    asyncio.create_task(run_screener_refresh())

    while True:
        await asyncio.sleep(SCREENER_REFRESH_SECONDS)
        await run_screener_refresh()
