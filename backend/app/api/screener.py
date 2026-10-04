from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.screener import ScreenerFilters, ScreenerResponse
from app.services.screener_snapshot_service import ScreenerSnapshotService

router = APIRouter(prefix="/screener", tags=["Stock Screener"])


def _filters(
    min_score: float,
    min_roe: float,
    max_pe: float,
    max_debt_to_equity: float,
    min_revenue_growth: float,
    min_profit_growth: float,
    min_market_cap: float,
    limit: int,
) -> ScreenerFilters:
    return ScreenerFilters(
        min_score=min_score,
        min_roe=min_roe,
        max_pe=max_pe,
        max_debt_to_equity=max_debt_to_equity,
        min_revenue_growth=min_revenue_growth,
        min_profit_growth=min_profit_growth,
        min_market_cap=min_market_cap,
        limit=limit,
        # Retained for backwards-compatible request models. The HTTP request no
        # longer uses this to trigger a full-universe calculation.
        universe_limit=5000,
    )


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
    universe_limit: int = Query(5000, ge=20, le=10000),
    db: Session = Depends(get_db),
):
    # Important: never call StockScreenerService here. The expensive calculation
    # is performed by screener_worker and persisted in ScreenerSnapshot.
    filters = _filters(
        min_score,
        min_roe,
        max_pe,
        max_debt_to_equity,
        min_revenue_growth,
        min_profit_growth,
        min_market_cap,
        limit,
    )
    total_universe, results, snapshot_at = ScreenerSnapshotService(db).get_results(filters)

    return ScreenerResponse(
        total_universe=total_universe,
        screened=len(results),
        results=results,
        data_source="Persistent StockSage screener snapshot built from NSE universe",
        methodology=(
            "Background snapshot: 50% fundamental, 20% valuation, 20% technical, "
            "10% analyst. HTTP requests only filter the persisted Top-N snapshot; "
            "they never query Yahoo/NSE or calculate indicators synchronously. "
            f"Snapshot time: {snapshot_at.isoformat() if snapshot_at else 'not yet available'}."
        ),
    )
