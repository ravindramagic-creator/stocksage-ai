from fastapi import APIRouter

from app.schemas.market_data import StockQuote
from app.services.market_data.ibja_gold_provider import IBJAGoldProvider
from app.services.market_data.nse_gift_nifty_provider import NSEGiftniftyProvider
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
    "CRUDE OIL": "CL=F",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI",
    # Market-regime indicators used by the main-page Market Pulse.
    "INDIA VIX": "^INDIAVIX",
    "USD/INR": "INR=X",
    "BRENT CRUDE": "BZ=F",
}

GIFT_NIFTY = "GIFT NIFTY"


def _get_gold_quote() -> StockQuote | None:
    try:
        return IBJAGoldProvider().get_quote("GOLD")
    except Exception:
        # Keep the dashboard available even when the Indian benchmark source
        # is temporarily unavailable.
        return None


def _get_gift_nifty_quote() -> StockQuote | None:
    try:
        return NSEGiftniftyProvider().get_quote(GIFT_NIFTY)
    except Exception:
        # Keep the rest of the market dashboard available if NSE's status feed
        # is temporarily unavailable.
        return None


@router.get(
    "/indices",
    response_model=list[StockQuote],
)
def get_indices():
    service = get_market_service()
    results: list[StockQuote] = []

    # Use the Indian benchmark directly instead of converting COMEX futures.
    gold = _get_gold_quote()
    if gold is not None:
        gold.symbol = "GOLD"
        results.append(gold)

    for name, provider_symbol in INDEX_SYMBOLS.items():
        try:
            quote = service.get_quote(provider_symbol)
            if quote is None:
                continue

            quote.symbol = name
            results.append(quote)
        except Exception:
            # One unavailable instrument must not hide the rest of the dashboard.
            continue

    # Keep the frontend's requested order: GIFT NIFTY after NIFTY SMALLCAP.
    gift_nifty = _get_gift_nifty_quote()
    if gift_nifty is not None:
        gift_nifty.symbol = GIFT_NIFTY

        # Nifty-related entries occupy the first four positions. Gold was added
        # separately above, so insert Gift Nifty before the commodity/global cards.
        results.insert(4, gift_nifty)

    # Return in deterministic dashboard order regardless of provider response
    # timing or temporary source failures.
    preferred_order = [
        "NIFTY50",
        "BANK NIFTY",
        "NIFTY MIDCAP",
        "NIFTY SMALLCAP",
        "GIFT NIFTY",
        "GOLD",
        "CRUDE OIL",
        "NASDAQ",
        "DOW JONES",
        "INDIA VIX",
        "USD/INR",
        "BRENT CRUDE",
    ]
    rank = {symbol: index for index, symbol in enumerate(preferred_order)}
    results.sort(key=lambda item: rank.get(item.symbol, len(preferred_order)))

    return results
