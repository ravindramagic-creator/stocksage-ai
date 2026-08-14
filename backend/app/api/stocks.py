from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.stock_repository import StockRepository
from app.schemas.stock import StockResponse

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
    repository = StockRepository(db)

    return repository.get_all()


@router.get(
    "/search",
    response_model=list[StockResponse],
)
def search_stocks(
    q: str,
    db: Session = Depends(get_db),
):
    repository = StockRepository(db)

    return repository.search(q)


@router.get(
    "/{symbol}",
    response_model=StockResponse,
)
def get_stock(
    symbol: str,
    db: Session = Depends(get_db),
):
    repository = StockRepository(db)

    stock = repository.get_by_symbol(symbol)

    if stock is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found",
        )

    return stock
