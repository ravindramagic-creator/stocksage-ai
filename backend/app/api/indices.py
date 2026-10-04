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
    # Market-regime indicators used by the main-page Market Pulse.
    "INDIA VIX": "^INDIAVIX",
    "USD/INR": "INR=X",
    "BRENT CRUDE": "BZ=F",
}

# Yahoo Finance quotes gold futures in USD per troy ounce. For an Indian
# dashboard, display the equivalent INR value per 10 grams, which is the
# conventional unit used for Indian gold pricing.
TROY_OUNCE_GRAMS = 31.1034768
GOLD_GRAMS = 10.0


def _gold_to_inr_per_10g(
    quote: StockQuote,
    usd_inr: StockQuote,
) -> StockQuote:
    fx = usd_inr.price

    if quote.price is None or fx is None or fx <= 0:
        return quote

    factor = fx * GOLD_GRAMS / TROY_OUNCE_GRAMS

    quote.price *= factor
    if quote.previous_close is not None:
        quote.previous_close *= factor
    if quote.open is not None:
        quote.open *= factor
    if quote.day_high is not None:
        quote.day_high *= factor
    if quote.day_low is not None:
        quote.day_low *= factor
    if quote.change is not None:
        quote.change *= factor

    quote.currency = "INR"
    return quote


@router.get(
    "/indices",
    response_model=list[StockQuote],
)
def get_indices():
    service = get_market_service()
    results: list[StockQuote] = []
    usd_inr: StockQuote | None = None

    # Fetch USD/INR once because it is also required to convert gold.
    try:
        usd_inr = service.get_quote(INDEX_SYMBOLS["USD/INR"])
    except Exception:
        usd_inr = None

    for name, provider_symbol in INDEX_SYMBOLS.items():
        try:
            quote = service.get_quote(provider_symbol)
            if quote is None:
                continue

            if name == "GOLD":
                if usd_inr is None or usd_inr.price is None:
                    # Do not expose an unlabeled USD gold value as INR.
                    continue
                quote = _gold_to_inr_per_10g(
                    quote,
                    usd_inr,
                )

            quote.symbol = name
            results.append(quote)
        except Exception:
            # One unavailable instrument must not hide the rest of the dashboard.
            continue

    return results
