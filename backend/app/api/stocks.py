from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.stock import StockResponse
from app.services.nse_universe_service import NSEUniverseService
from app.services.stock_service import StockService


router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"],
)


@router.get(
    "",
    response_model=list[StockResponse],
)
def get_stocks(
    db: Session = Depends(get_db),
):
    service = StockService(db)
    return service.get_all()


@router.get(
    "/search",
    response_model=list[StockResponse],
)
def search_stocks(
    q: str,
    db: Session = Depends(get_db),
):
    service = StockService(db)

    if not q.strip():
        return []

    return service.search(q)


@router.post(
    "/universe/refresh",
)
def refresh_nse_universe(
    db: Session = Depends(get_db),
):
    """Manually refresh the local NSE equity master."""
    try:
        source_count = NSEUniverseService().refresh_database(db)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to refresh NSE universe: {exc}",
        ) from exc

    database_count = NSEUniverseService.database_count(db)
    return {
        "source_count": source_count,
        "database_count": database_count,
        "exchange": "NSE",
    }


@router.get(
    "/{symbol}",
    response_model=StockResponse,
)
def get_stock(
    symbol: str,
    db: Session = Depends(get_db),
):
    service = StockService(db)

    stock = service.get_by_symbol(symbol)

    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found",
        )

    return stock
