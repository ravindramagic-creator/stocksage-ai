from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.subscription import Subscription


def get_active_symbols(
    db: Session,
) -> list[str]:

    statement = (
        select(Stock.symbol)
        .join(
            Subscription,
            Subscription.stock_id
            == Stock.id,
        )
        .where(
            Subscription.enabled.is_(True)
        )
        .order_by(Stock.symbol)
    )

    return list(
        db.scalars(statement).all()
    )
