from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.nse_universe_service import NSEUniverseService

logger = logging.getLogger("stocksage.universe_worker")

UNIVERSE_REFRESH_SECONDS = 24 * 60 * 60


def _run_universe_refresh_sync() -> None:
    db = SessionLocal()
    try:
        count = NSEUniverseService().refresh_database(db)
        logger.info(
            "NSE universe refresh completed: %d symbols",
            count,
        )
    except Exception:
        logger.exception(
            "NSE universe refresh failed; keeping existing universe"
        )
    finally:
        db.close()


async def run_universe_refresh() -> None:
    # NSE requests and database writes are synchronous and must not block the
    # FastAPI event loop.
    await asyncio.to_thread(
        _run_universe_refresh_sync
    )


async def universe_worker() -> None:
    logger.info("NSE universe worker started")

    # Universe data is persisted already; refresh in the background after the
    # API is ready instead of blocking application startup.
    await asyncio.sleep(15)
    await run_universe_refresh()

    while True:
        await asyncio.sleep(
            UNIVERSE_REFRESH_SECONDS
        )
        await run_universe_refresh()
