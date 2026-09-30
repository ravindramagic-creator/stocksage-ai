import asyncio
import logging

from app.db.database import SessionLocal
from app.providers.vahan_retail_provider import VahanRetailProvider
from app.services.auto_sales_ingestion import AutoSalesIngestion

logger = logging.getLogger("stocksage.auto_sales_worker")

# Refresh once per day. The provider's current month can change daily because
# VAHAN registrations are updated during the month.
AUTO_REFRESH_SECONDS = 24 * 60 * 60


async def run_auto_sales_refresh() -> None:
    db = SessionLocal()
    try:
        provider = VahanRetailProvider()
        ingestion = AutoSalesIngestion(db, provider)
        records = provider.fetch_history()

        for record in records:
            ingestion.repository.upsert(record)

        db.commit()
        logger.info("Auto-sales refresh completed: %d records", len(records))
    except Exception:
        db.rollback()
        logger.exception("Auto-sales refresh failed")
    finally:
        db.close()


async def auto_sales_worker() -> None:
    logger.info("Auto-sales worker started")

    while True:
        await run_auto_sales_refresh()
        await asyncio.sleep(AUTO_REFRESH_SECONDS)
