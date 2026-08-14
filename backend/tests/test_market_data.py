from datetime import datetime, timezone

from app.schemas.market_data import (
    StockQuote,
)


def test_stock_quote_schema():
    quote = StockQuote(
        symbol="HAL",
        price=5000.0,
        previous_close=4900.0,
        open=4950.0,
        day_high=5050.0,
        day_low=4920.0,
        volume=100000,
        change=100.0,
        change_percent=2.04,
        currency="INR",
        market_state=None,
        updated_at=datetime.now(timezone.utc),
    )

    assert quote.symbol == "HAL"
    assert quote.price == 5000.0
    assert quote.change == 100.0
