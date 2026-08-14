from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.stock import StockResponse
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


@router.get(
    "/{symbol}",
    response_model=StockResponse,
)
def get_stock(
    symbol: str,
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException

    service = StockService(db)

    stock = service.get_by_symbol(symbol)

    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found",
        )

    return stock
