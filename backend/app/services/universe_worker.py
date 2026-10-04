from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.nse_universe_service import NSEUniverseService

logger = logging.getLogger("stocksage.universe_worker")

# The NSE equity master changes as listings, delistings and symbol changes occur.
# Refresh once per day rather than on every API request.
UNIVERSE_REFRESH_SECONDS = 24 * 60 * 60


async def run_universe_refresh() -> None:
    db = SessionLocal()
    try:
        count = NSEUniverseService().refresh_database(db)
        logger.info("NSE universe refresh completed: %d symbols", count)
    except Exception:
        logger.exception("NSE universe refresh failed; keeping existing universe")
    finally:
        db.close()


async def universe_worker() -> None:
    logger.info("NSE universe worker started")

    # Refresh immediately at startup. A failure is non-fatal because the last
    # successful database snapshot remains usable.
    await run_universe_refresh()

    while True:
        await asyncio.sleep(UNIVERSE_REFRESH_SECONDS)
        await run_universe_refresh()
