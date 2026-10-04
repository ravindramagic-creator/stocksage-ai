from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.screener import ScreenerFilters, ScreenerResponse
from app.services.screener_service import StockScreenerService


router = APIRouter(
    prefix="/screener",
    tags=["Stock Screener"],
)


@router.get("", response_model=ScreenerResponse)
def get_screener(
    min_score: float = Query(60, ge=0, le=100),
    max_pe: float = Query(45, ge=0, le=500),
    min_revenue_growth: float = Query(10, ge=-100, le=500),
    min_profit_growth: float = Query(10, ge=-100, le=500),
    limit: int = Query(20, ge=1, le=100),
    universe_limit: int = Query(250, ge=20, le=1000),
    db: Session = Depends(get_db),
):
    filters = ScreenerFilters(
        min_score=min_score,
        max_pe=max_pe,
        min_revenue_growth=min_revenue_growth,
        min_profit_growth=min_profit_growth,
        limit=limit,
        universe_limit=universe_limit,
    )

    total_universe, results = StockScreenerService(db).screen(filters)

    return ScreenerResponse(
        total_universe=total_universe,
        screened=len(results),
        results=results,
        data_source="StockSage database + market quote provider",
        methodology=(
            "35% growth, 25% earnings quality, 20% trailing PE valuation, "
            "20% short-term momentum. Missing data is not invented."
        ),
    )
