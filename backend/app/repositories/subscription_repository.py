from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.subscription import Subscription


class SubscriptionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
    ) -> list[Subscription]:

        statement = (
            select(Subscription)
            .where(
                Subscription.enabled.is_(True)
            )
            .order_by(
                Subscription.created_at.desc()
            )
        )

        return list(
            self.db.scalars(statement).all()
        )

    def get_by_symbol(
        self,
        symbol: str,
    ) -> Subscription | None:

        statement = (
            select(Subscription)
            .join(Subscription.stock)
            .where(
                Stock.symbol == symbol.upper()
            )
        )

        return self.db.scalars(
            statement
        ).first()

    def create(
        self,
        stock: Stock,
    ) -> Subscription:

        subscription = Subscription(
            stock_id=stock.id,
            enabled=True,
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def disable(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.enabled = False

        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def enable(
        self,
        subscription: Subscription,
    ) -> Subscription:

        subscription.enabled = True

        self.db.commit()
        self.db.refresh(subscription)

        return subscription
