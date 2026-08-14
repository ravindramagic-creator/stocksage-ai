from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.services.subscription_service import (
    SubscriptionService,
)


router = APIRouter(
    prefix="/subscriptions",
    tags=["Subscriptions"],
)


@router.get(
    "",
    response_model=list[
        SubscriptionResponse
    ],
)
def get_subscriptions(
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)

    return service.get_subscriptions()


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def subscribe(
    request: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    symbol = request.symbol.strip()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required",
        )

    service = SubscriptionService(db)

    return service.subscribe(
           symbol=symbol,
           company_name=request.company_name,
           exchange=request.exchange,
           sector=request.sector,
   )

@router.delete(
    "/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unsubscribe(
    symbol: str,
    db: Session = Depends(get_db),
):
    service = SubscriptionService(db)

    subscription = service.unsubscribe(
        symbol
    )

    if subscription is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Stock '{symbol}' is not "
                "subscribed"
            ),
        )
