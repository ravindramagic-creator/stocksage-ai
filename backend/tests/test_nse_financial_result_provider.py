from datetime import date
from decimal import Decimal

from app.services.nse_financial_result_provider import (
    NSEFinancialResultProvider,
)


def test_to_decimal():

    provider = (
        NSEFinancialResultProvider()
    )

    assert (
        provider.to_decimal(
            "12,345.67"
        )
        == Decimal("12345.67")
    )


def test_to_date():

    provider = (
        NSEFinancialResultProvider()
    )

    assert (
        provider.to_date(
            "30-Jun-2026"
        )
        == date(
            2026,
            6,
            30,
        )
    )


def test_parse_result_row():

    provider = (
        NSEFinancialResultProvider()
    )

    row = {
        "re_to_dt": "30-Jun-2026",
        "re_total_inc": "100000",
        "re_net_profit": "10000",
        "re_eps": "25.50",
    }

    result = (
        provider.parse_result_row(
            row
        )
    )

    assert (
        result["period_ended"]
        == date(2026, 6, 30)
    )

    assert (
        result["revenue"]
        == Decimal("10000000000")
    )

    assert (
        result["pat"]
        == Decimal("1000000000")
    )

    assert (
        result["eps"]
        == Decimal("25.50")
    )
