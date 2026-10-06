from __future__ import annotations

import asyncio
import logging

from app.db.database import SessionLocal
from app.providers.vahan_retail_provider import VahanRetailProvider
from app.services.auto_sales_ingestion import AutoSalesIngestion


logger = logging.getLogger("stocksage.auto_sales_worker")

AUTO_REFRESH_SECONDS = 24 * 60 * 60


def _run_auto_sales_refresh_sync(
    segment: str | None = None,
) -> int:
    db = SessionLocal()

    try:
        provider = VahanRetailProvider()
        ingestion = AutoSalesIngestion(
            db,
            provider,
        )
        records = provider.fetch_history(
            segment=segment,
        )

        if not records:
            logger.warning(
                "Auto-sales refresh returned no records%s",
                f" for segment={segment}" if segment else "",
            )
            return 0

        for record in records:
            ingestion.repository.upsert(record)

        db.commit()

        logger.info(
            "Auto-sales refresh completed: %d records",
            len(records),
        )
        return len(records)
    except Exception:
        db.rollback()
        logger.exception(
            "Auto-sales refresh failed; existing data was preserved",
        )
        return 0
    finally:
        db.close()


async def run_auto_sales_refresh(
    segment: str | None = None,
) -> int:
    # Vahan requests and database writes are synchronous. Running them in the
    # asyncio event loop can make every frontend request wait for the provider.
    return await asyncio.to_thread(
        _run_auto_sales_refresh_sync,
        segment,
    )


async def auto_sales_worker() -> None:
    logger.info("Auto-sales worker started")

    # Auto-sales is daily data. Delay the first refresh so the HTTP API gets
    # priority during application startup.
    await asyncio.sleep(60)

    while True:
        try:
            await run_auto_sales_refresh()
        except Exception:
            logger.exception(
                "Unexpected auto-sales worker error",
            )

        await asyncio.sleep(
            AUTO_REFRESH_SECONDS,
        )
