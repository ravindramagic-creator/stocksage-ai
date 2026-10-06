from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.market_regime import MarketRegimeResponse
from app.services.market_regime_service import MarketRegimeService


router = APIRouter(
    prefix="/market-regime",
    tags=["Market Regime"],
)


@router.get(
    "",
    response_model=MarketRegimeResponse,
)
def get_market_regime(
    db: Session = Depends(get_db),
):
    return MarketRegimeService(db).get()
