from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, HTTPException, Query

from app.schemas.market_data import HistoricalPrices, StockQuote
from app.services.market_service import get_market_service


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

    service = get_market_service()

    try:
        quote = service.get_quote(symbol)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to retrieve market data "
                f"for '{symbol}'"
            ),
        ) from exc

    if quote is None or quote.price is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for '{symbol}'",
        )

    return quote


@router.get(
    "/quotes",
    response_model=list[StockQuote],
)
def get_quotes(
    symbols: str = Query(
        ...,
        description="Comma-separated NSE symbols, maximum 50",
    ),
):
    requested = [
        symbol.strip().upper()
        for symbol in symbols.split(",")
        if symbol.strip()
    ]

    # Preserve request order while removing duplicates.
    requested = list(dict.fromkeys(requested))

    if not requested:
        return []

    if len(requested) > 50:
        raise HTTPException(
            status_code=400,
            detail="A maximum of 50 symbols can be requested",
        )

    service = get_market_service()
    results_by_symbol: dict[str, StockQuote] = {}

    # Subscriptions used to trigger one browser request per stock. Fetch all
    # requested quotes concurrently on the backend instead.
    with ThreadPoolExecutor(
        max_workers=min(8, len(requested)),
        thread_name_prefix="watchlist-quote",
    ) as executor:
        futures = {
            executor.submit(service.get_quote, symbol): symbol
            for symbol in requested
        }

        for future in as_completed(futures):
            symbol = futures[future]

            try:
                quote = future.result()
                if quote is not None and quote.price is not None:
                    results_by_symbol[symbol] = quote
            except Exception:
                # One unavailable stock must not fail the whole watchlist.
                continue

    return [
        results_by_symbol[symbol]
        for symbol in requested
        if symbol in results_by_symbol
    ]


@router.get(
    "/history/{symbol}",
    response_model=HistoricalPrices,
)
def get_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
):
    allowed_periods = {
        "1d",
        "5d",
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "5y",
        "10y",
        "max",
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
            detail=f"Unsupported interval: {interval}",
        )

    service = get_market_service()

    try:
        return service.get_history(
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
