from fastapi import APIRouter, HTTPException

from app.schemas.market_data import (
    HistoricalPrices,
    StockQuote,
)
from app.services.market_data.factory import (
    get_market_data_provider,
)

router = APIRouter(
    prefix="/market",
    tags=["Market Data"],
)


@router.get(
    "/quote/{symbol}",
    response_model=StockQuote,
)
def get_quote(symbol: str):

    symbol = symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required",
        )

    provider = get_market_data_provider()

    try:
        quote = provider.get_quote(symbol)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to retrieve market data "
                f"for '{symbol}'"
            ),
        ) from exc

    if quote.price is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No market data found for "
                f"'{symbol}'"
            ),
        )

    return quote


@router.get(
    "/history/{symbol}",
    response_model=HistoricalPrices,
)
def get_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
):

    symbol = symbol.strip().upper()

    allowed_periods = {
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y",
    }

    allowed_intervals = {
        "1m",
        "5m",
        "15m",
        "30m",
        "60m",
        "1d",
        "1wk",
        "1mo",
    }

    if period not in allowed_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported period: {period}",
        )

    if interval not in allowed_intervals:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported interval: "
                f"{interval}"
            ),
        )

    provider = get_market_data_provider()

    try:
        history = provider.get_history(
            symbol=symbol,
            period=period,
            interval=interval,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to retrieve historical "
                f"data for '{symbol}'"
            ),
        ) from exc

    return history
