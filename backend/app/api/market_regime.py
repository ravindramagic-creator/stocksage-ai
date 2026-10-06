from fastapi import APIRouter

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
def get_market_regime():
    # MarketRegimeService uses the persisted market snapshot and cached quote
    # layer. The endpoint remains lightweight enough for dashboard polling.
    return MarketRegimeService().get()
