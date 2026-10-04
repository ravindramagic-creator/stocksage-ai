from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.screener import ScreenerFilters, ScreenerResponse
from app.services.screener_service import StockScreenerService

router = APIRouter(prefix="/screener", tags=["Stock Screener"])


@router.get("", response_model=ScreenerResponse)
def get_screener(
    min_score: float = Query(60, ge=0, le=100),
    min_roe: float = Query(15, ge=-100, le=200),
    max_pe: float = Query(45, ge=0, le=500),
    max_debt_to_equity: float = Query(1.5, ge=0, le=20),
    min_revenue_growth: float = Query(10, ge=-100, le=500),
    min_profit_growth: float = Query(10, ge=-100, le=500),
    min_market_cap: float = Query(5000, ge=0),
    limit: int = Query(10, ge=1, le=100),
    universe_limit: int = Query(100, ge=20, le=1000),
    db: Session = Depends(get_db),
):
    filters = ScreenerFilters(
        min_score=min_score,
        min_roe=min_roe,
        max_pe=max_pe,
        max_debt_to_equity=max_debt_to_equity,
        min_revenue_growth=min_revenue_growth,
        min_profit_growth=min_profit_growth,
        min_market_cap=min_market_cap,
        limit=limit,
        universe_limit=universe_limit,
    )
    total_universe, results = StockScreenerService(db).screen(filters)
    return ScreenerResponse(
        total_universe=total_universe,
        screened=len(results),
        results=results,
        data_source="StockSage financial database + Yahoo Finance market/fundamental provider",
        methodology=(
            "50% fundamental (growth, ROE, ROCE, leverage), 20% valuation (PE, PEG, PB), "
            "20% technical (50/200 DMA, RSI-14, 6-month momentum), 10% analyst (beat rate + target upside). "
            "Missing metrics are excluded from component calculations and surfaced via completeness."
        ),
    )
