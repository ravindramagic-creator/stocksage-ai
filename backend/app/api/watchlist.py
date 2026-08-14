from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.stock_repository import StockRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistResponse,
)

router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"],
)


@router.get(
    "",
    response_model=list[WatchlistResponse],
)
def get_watchlist(
    db: Session = Depends(get_db),
):
    repository = WatchlistRepository(db)

    return repository.get_all()


@router.post(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_watchlist(
    request: WatchlistCreate,
    db: Session = Depends(get_db),
):
    stock_repository = StockRepository(db)
    watchlist_repository = WatchlistRepository(db)

    symbol = request.symbol.upper().strip()

    stock = stock_repository.get_by_symbol(symbol)

    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found",
        )

    existing = watchlist_repository.get_by_symbol(symbol)

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Stock '{symbol}' is already in the watchlist",
        )

    return watchlist_repository.add(stock)


@router.delete(
    "/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
):
    repository = WatchlistRepository(db)

    item = repository.get_by_symbol(symbol)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' is not in the watchlist",
        )

    repository.delete(item)
