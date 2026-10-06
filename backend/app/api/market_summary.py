from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.market_summary import MarketSummaryResponse
from app.services.market_summary_service import MarketSummaryService


router = APIRouter(
    prefix="/market-summary",
    tags=["Market Summary"],
)


@router.get(
    "",
    response_model=MarketSummaryResponse,
)
def get_market_summary(
    db: Session = Depends(get_db),
):
    return MarketSummaryService(db).get()
