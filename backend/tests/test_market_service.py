from datetime import datetime, timezone
from unittest.mock import Mock

from app.schemas.market_data import StockQuote
from app.services.market_service import MarketService


def test_market_service_returns_cached_quote():
    provider = Mock()

    provider.get_quote.return_value = StockQuote(
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

    service = MarketService()
    service.provider = provider

    first = service.get_quote("HAL")
    second = service.get_quote("HAL")

    assert first.price == 5000.0
    assert second.price == 5000.0

    provider.get_quote.assert_called_once_with(
        "HAL"
    )
