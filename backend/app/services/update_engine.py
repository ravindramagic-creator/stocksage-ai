from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.market_service import (
    get_market_service,
)
from app.services.update_service import (
    UpdateService,
)


PRICE_CHANGE_THRESHOLD = 3.0


class UpdateEngine:

    def __init__(self, db: Session):

        self.db = db

        self.market_service = (
            get_market_service()
        )

        self.update_service = (
            UpdateService(db)
        )

    def process_symbol(
        self,
        symbol: str,
    ):

        symbol = symbol.strip().upper()

        quote = (
            self.market_service.get_quote(
                symbol
            )
        )

        if (
            quote.price is None
            or quote.previous_close is None
        ):
            return []

        change_percent = (
            quote.change_percent or 0
        )

        events = []

        if abs(change_percent) >= PRICE_CHANGE_THRESHOLD:

            direction = (
                "up"
                if change_percent > 0
                else "down"
            )

            title = (
                f"{symbol} is up "
                f"{abs(change_percent):.2f}%"
                if direction == "up"
                else
                f"{symbol} is down "
                f"{abs(change_percent):.2f}%"
            )

            description = (
                f"{symbol} moved "
                f"{change_percent:+.2f}% "
                f"from the previous close."
            )

            # Bucket by calendar day and
            # direction so polling doesn't
            # create duplicate events.
            event_key = (
                f"PRICE:{symbol}:"
                f"{datetime.now(timezone.utc).date()}:"
                f"{direction}"
            )

            event = (
                self.update_service.create_event(
                    symbol=symbol,
                    event_type="PRICE_MOVE",
                    title=title,
                    description=description,
                    source="Market Data",
                    old_value=quote.previous_close,
                    new_value=quote.price,
                    event_key=event_key,
                    event_time=(
                        quote.updated_at
                        or datetime.now(
                            timezone.utc
                        )
                    ),
                )
            )

            if event:
                events.append(event)

        return events
