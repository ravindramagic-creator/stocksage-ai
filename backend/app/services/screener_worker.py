from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.screener_snapshot_service import ScreenerSnapshotService

logger = logging.getLogger("stocksage.screener_worker")

SCREENER_REFRESH_SECONDS = 15 * 60


def _run_screener_refresh_sync() -> None:
    db = SessionLocal()
    try:
        count = ScreenerSnapshotService(db).refresh(
            universe_limit=5000
        )
        logger.info(
            "Screener snapshot refreshed: %d stocks",
            count,
        )
    except Exception:
        logger.exception(
            "Screener snapshot refresh failed; keeping last snapshot"
        )
    finally:
        db.close()


async def run_screener_refresh() -> None:
    # The snapshot calculation is synchronous database work. Never execute it
    # directly in the asyncio event loop.
    await asyncio.to_thread(
        _run_screener_refresh_sync
    )


async def screener_worker() -> None:
    logger.info(
        "Screener snapshot worker started"
    )

    # Do not compete with the initial page load for CPU/database resources.
    await asyncio.sleep(20)
    await run_screener_refresh()

    while True:
        await asyncio.sleep(
            SCREENER_REFRESH_SECONDS
        )
        await run_screener_refresh()
