from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter

from app.schemas.market_data import StockQuote
from app.services.market_data.ibja_gold_provider import IBJAGoldProvider
from app.services.market_data.nse_gift_nifty_provider import NSEGiftniftyProvider
from app.services.market_cache import market_cache
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
    "INDIA VIX": "^INDIAVIX",
    "USD/INR": "INR=X",
    "BRENT CRUDE": "BZ=F",
}

GIFT_NIFTY = "GIFT NIFTY"

INDICES_CACHE_KEY = "dashboard:market-indices"
INDICES_CACHE_TTL = 30

PREFERRED_ORDER = [
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


def _get_gold_quote() -> StockQuote | None:
    try:
        cached = market_cache.get("dashboard:gold")
        if cached is not None:
            return cached

        quote = IBJAGoldProvider().get_quote("GOLD")
        market_cache.set(
            "dashboard:gold",
            quote,
            INDICES_CACHE_TTL,
        )
        return quote
    except Exception:
        return None


def _get_gift_nifty_quote() -> StockQuote | None:
    try:
        cached = market_cache.get("dashboard:gift-nifty")
        if cached is not None:
            return cached

        quote = NSEGiftniftyProvider().get_quote(GIFT_NIFTY)
        market_cache.set(
            "dashboard:gift-nifty",
            quote,
            INDICES_CACHE_TTL,
        )
        return quote
    except Exception:
        return None


def _get_yahoo_quote(
    name: str,
    provider_symbol: str,
) -> StockQuote | None:
    try:
        quote = get_market_service().get_quote(provider_symbol)
        if quote is None:
            return None
        quote.symbol = name
        return quote
    except Exception:
        return None


@router.get(
    "/indices",
    response_model=list[StockQuote],
)
def get_indices():
    cached = market_cache.get(INDICES_CACHE_KEY)
    if cached is not None:
        return cached

    results: list[StockQuote] = []

    # The market cards are independent. Fetch Yahoo symbols concurrently
    # instead of waiting for 10 sequential upstream requests.
    with ThreadPoolExecutor(
        max_workers=5,
        thread_name_prefix="market-card",
    ) as executor:
        futures = [
            executor.submit(
                _get_yahoo_quote,
                name,
                provider_symbol,
            )
            for name, provider_symbol in INDEX_SYMBOLS.items()
        ]

        for future in as_completed(futures):
            quote = future.result()
            if quote is not None:
                results.append(quote)

        # The Indian gold benchmark and GIFT Nifty are separate upstream
        # providers, so fetch them concurrently with the other cards.
        gold_future = executor.submit(_get_gold_quote)
        gift_future = executor.submit(_get_gift_nifty_quote)

        gold = gold_future.result()
        gift_nifty = gift_future.result()

    if gift_nifty is not None:
        gift_nifty.symbol = GIFT_NIFTY
        results.append(gift_nifty)

    if gold is not None:
        gold.symbol = "GOLD"
        results.append(gold)

    rank = {
        symbol: index
        for index, symbol in enumerate(PREFERRED_ORDER)
    }
    results.sort(
        key=lambda item: rank.get(
            item.symbol,
            len(PREFERRED_ORDER),
        )
    )

    market_cache.set(
        INDICES_CACHE_KEY,
        results,
        INDICES_CACHE_TTL,
    )

    return results
