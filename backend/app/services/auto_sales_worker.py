import asyncio
import logging
from datetime import date

from app.db.database import SessionLocal
from app.providers.vahan_retail_provider import VahanRetailProvider
from app.services.auto_sales_ingestion import AutoSalesIngestion

logger = logging.getLogger("stocksage.auto_sales_worker")

# Refresh once per day. The current month can change during the month.
AUTO_REFRESH_SECONDS = 24 * 60 * 60


async def run_auto_sales_refresh(segment: str | None = None) -> int:
    """Refresh auto-sales data without allowing provider failures to break startup."""
    db = SessionLocal()
    try:
        provider = VahanRetailProvider()
        ingestion = AutoSalesIngestion(db, provider)
        records = provider.fetch_history(segment=segment)

        if not records:
            logger.warning(
                "Auto-sales refresh returned no records%s",
                f" for segment={segment}" if segment else "",
            )
            return 0

        for record in records:
            ingestion.repository.upsert(record)

        db.commit()
        logger.info("Auto-sales refresh completed: %d records", len(records))
        return len(records)
    except Exception:
        db.rollback()
        logger.exception("Auto-sales refresh failed; existing data was preserved")
        return 0
    finally:
        db.close()


async def auto_sales_worker() -> None:
    logger.info("Auto-sales worker started")

    # A failure in an external data source must never prevent FastAPI from
    # starting. The worker retries on the next scheduled interval.
    while True:
        try:
            await run_auto_sales_refresh()
        except Exception:
            logger.exception("Unexpected auto-sales worker error")

        await asyncio.sleep(AUTO_REFRESH_SECONDS)
