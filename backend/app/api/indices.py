from fastapi import APIRouter

from app.schemas.market_data import StockQuote
from app.services.market_service import get_market_service


router = APIRouter(
    prefix="/market",
    tags=["Market Data"],
)


INDEX_SYMBOLS = {
    "NIFTY50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "NIFTY MIDCAP": "^NSEMDCP50",
    "NIFTY SMALLCAP": "^CNXSC",
    "GIFT NIFTY": "NIFTY1.NS",
    "GOLD": "GC=F",
    "CRUDE OIL": "CL=F",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI",
}


@router.get(
    "/indices",
    response_model=list[StockQuote],
)
def get_indices():
    service = get_market_service()
    results: list[StockQuote] = []

    for name, provider_symbol in INDEX_SYMBOLS.items():
        try:
            quote = service.get_quote(provider_symbol)
            if quote is None:
                continue
            quote.symbol = name
            results.append(quote)
        except Exception:
            continue

    return results
