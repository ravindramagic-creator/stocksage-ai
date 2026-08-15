import asyncio
import logging

from app.db.database import SessionLocal

from app.services.event_engine import (
    EventEngine,
)

from app.services.subscription_symbols import (
    get_active_symbols,
)

from app.services.update_engine import (
    UpdateEngine,
)


logger = logging.getLogger(
    "stocksage.update_worker"
)


UPDATE_INTERVAL_SECONDS = 60


async def run_update_cycle():

    db = SessionLocal()

    try:

        symbols = get_active_symbols(
            db
        )

        if not symbols:

            logger.info(
                "No active subscriptions"
            )

            return

        logger.info(
            "Processing %d subscribed stocks",
            len(symbols),
        )

        price_engine = UpdateEngine(
            db
        )

        event_engine = EventEngine(
            db
        )

        for symbol in symbols:

            # --------------------------------
            # PRICE EVENTS
            # --------------------------------

            try:

                price_events = (
                    price_engine
                    .process_symbol(
                        symbol
                    )
                )

                if price_events:

                    logger.info(
                        "%s: %d price events",
                        symbol,
                        len(price_events),
                    )

            except Exception:

                logger.exception(
                    "Price processing failed "
                    "for %s",
                    symbol,
                )

            # --------------------------------
            # NEWS / CORPORATE EVENTS
            # --------------------------------

            try:

                events = (
                    event_engine
                    .process_symbol(
                        symbol
                    )
                )

                if events:

                    logger.info(
                        "%s: %d external events",
                        symbol,
                        len(events),
                    )

            except Exception:

                logger.exception(
                    "Event processing failed "
                    "for %s",
                    symbol,
                )

    finally:

        db.close()


async def update_worker():

    logger.info(
        "StockSage update worker started"
    )

    while True:

        try:

            await run_update_cycle()

        except Exception:

            logger.exception(
                "Update cycle failed"
            )

        await asyncio.sleep(
            UPDATE_INTERVAL_SECONDS
        )
