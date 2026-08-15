import logging

from sqlalchemy.orm import Session

from app.services.events.nse_provider import (
    NSEEventProvider,
)

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

        self.providers = [
            NSEEventProvider(),
            YFinanceEventProvider(),
        ]

    def process_symbol(
        self,
        symbol: str,
    ):

        symbol = symbol.strip().upper()

        all_events = []

        for provider in self.providers:

            provider_name = (
                provider.__class__.__name__
            )

            try:

                events = provider.get_events(
                    symbol
                )

                logger.info(
                    "%s returned %d events "
                    "for %s",
                    provider_name,
                    len(events),
                    symbol,
                )

                all_events.extend(
                    events
                )

            except Exception:

                logger.exception(
                    "%s failed for %s",
                    provider_name,
                    symbol,
                )

        created_events = []

        for event in all_events:

            try:

                created = (
                    self.update_service
                    .create_event(
                        symbol=event.symbol,
                        event_type=event.event_type,
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
