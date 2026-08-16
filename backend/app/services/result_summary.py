from decimal import Decimal


def format_growth(
    value: Decimal | None,
) -> str:

    if value is None:
        return "N/A"

    sign = "+" if value >= 0 else ""

    return f"{sign}{value:.1f}%"


def generate_summary(
    *,
    symbol: str,
    revenue_yoy: Decimal | None,
    ebitda_yoy: Decimal | None,
    pat_yoy: Decimal | None,
) -> str:

    parts = []

    if revenue_yoy is not None:

        parts.append(
            "Revenue "
            f"{format_growth(revenue_yoy)} YoY"
        )

    if ebitda_yoy is not None:

        parts.append(
            "EBITDA "
            f"{format_growth(ebitda_yoy)} YoY"
        )

    if pat_yoy is not None:

        parts.append(
            "PAT "
            f"{format_growth(pat_yoy)} YoY"
        )

    if not parts:

        return (
            f"{symbol}: Financial results "
            "available."
        )

    return (
        f"{symbol}: "
        + ", ".join(parts)
        + "."
    )
