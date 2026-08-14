from fastapi import APIRouter

from app.schemas.market_data import StockQuote
from app.services.market_service import (
    get_market_service,
)


router = APIRouter(
    prefix="/market",
    tags=["Market Data"],
)


INDEX_SYMBOLS = {
    "NIFTY50": "^NSEI",
    "SENSEX": "^BSESN",
}


@router.get(
    "/indices",
    response_model=list[StockQuote],
)
def get_indices():

    service = get_market_service()

    results = []

    for name, yahoo_symbol in (
        INDEX_SYMBOLS.items()
    ):

        try:
            quote = service.get_quote(
                yahoo_symbol
            )

            quote.symbol = name

            results.append(quote)

        except Exception:
            continue

    return results
