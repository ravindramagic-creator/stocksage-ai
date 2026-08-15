import logging

from sqlalchemy.orm import Session

from app.services.events.yfinance_provider import (
    YFinanceEventProvider,
)
from app.services.update_service import (
    UpdateService,
)


logger = logging.getLogger(
    "stocksage.event_engine"
)


class EventEngine:

    def __init__(
        self,
        db: Session,
    ):

        self.update_service = (
            UpdateService(db)
        )

        self.provider = (
            YFinanceEventProvider()
        )

    def process_symbol(
        self,
        symbol: str,
    ):

        symbol = symbol.strip().upper()

        logger.info(
            "Checking events for %s",
            symbol,
        )

        try:

            events = (
                self.provider.get_events(
                    symbol
                )
            )

        except Exception:

            logger.exception(
                "Failed retrieving events for %s",
                symbol,
            )

            return []

        created_events = []

        for event in events:

            try:

                created = (
                    self.update_service
                    .create_event(
                        symbol=event.symbol,
                        event_type=(
                            event.event_type
                        ),
                        title=event.title,
                        description=(
                            event.description
                        ),
                        source=event.source,
                        source_url=(
                            event.source_url
                        ),
                        old_value=(
                            event.old_value
                        ),
                        new_value=(
                            event.new_value
                        ),
                        event_key=(
                            event.event_key
                        ),
                        event_time=(
                            event.event_time
                        ),
                    )
                )

                if created:
                    created_events.append(
                        created
                    )

            except Exception:

                logger.exception(
                    "Failed storing event "
                    "for %s",
                    symbol,
                )

        logger.info(
            "%s: %d new events",
            symbol,
            len(created_events),
        )

        return created_events
