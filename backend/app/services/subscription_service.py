from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.repositories.stock_repository import (
    StockRepository,
)
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.services.stock_discovery import (
    StockDiscoveryService,
)


class SubscriptionService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.stock_repository = (
            StockRepository(db)
        )

        self.subscription_repository = (
            SubscriptionRepository(db)
        )

    def subscribe(
        self,
        symbol: str,
        company_name: str | None = None,
        exchange: str = "NSE",
        sector: str | None = None,
    ):

        symbol = symbol.strip().upper()

        stock = (
            self.stock_repository
            .get_by_symbol(symbol)
        )

        # Stock isn't in our DB yet.
        if stock is None:

            stock = Stock(
                symbol=symbol,
                company_name=(
                    company_name
                    or symbol
                ),
                exchange=exchange,
                sector=sector,
            )

            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)

        existing = (
            self.subscription_repository
            .get_by_symbol(symbol)
        )

        if existing:

            if existing.enabled:
                return existing

            return (
                self.subscription_repository
                .enable(existing)
            )

        return (
            self.subscription_repository
            .create(stock)
        )

    def unsubscribe(
        self,
        symbol: str,
    ):

        symbol = symbol.strip().upper()

        subscription = (
            self.subscription_repository
            .get_by_symbol(symbol)
        )

        if subscription is None:
            return None

        if not subscription.enabled:
            return subscription

        return (
            self.subscription_repository
            .disable(subscription)
        )

    def get_subscriptions(self):

        return (
            self.subscription_repository
            .get_all()
        )
