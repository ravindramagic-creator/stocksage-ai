from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.services.market_snapshot_service import MarketSnapshotService

logger = logging.getLogger("stocksage.market_snapshot_worker")

BATCH_SIZE = 12
REFRESH_INTERVAL_SECONDS = 60


def _run_market_snapshot_cycle_sync() -> int:
    db = SessionLocal()
    try:
        count = MarketSnapshotService(
            db,
            stale_minutes=15,
        ).refresh_stale(limit=BATCH_SIZE)
        logger.info(
            "Incremental market snapshot refresh: %d symbols",
            count,
        )
        return count
    except Exception:
        logger.exception(
            "Incremental market snapshot refresh failed"
        )
        return 0
    finally:
        db.close()


async def run_market_snapshot_cycle() -> int:
    # yfinance/requests and SQLAlchemy are synchronous. Running them directly
    # inside the async worker blocks FastAPI's event loop and makes the entire
    # web app appear frozen while a batch is refreshed.
    return await asyncio.to_thread(
        _run_market_snapshot_cycle_sync
    )


async def market_snapshot_worker() -> None:
    logger.info(
        "Incremental market snapshot worker started"
    )

    # Let the API become responsive before the first provider-heavy refresh.
    await asyncio.sleep(10)

    while True:
        await run_market_snapshot_cycle()
        await asyncio.sleep(
            REFRESH_INTERVAL_SECONDS
        )
