from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


class FinancialResultParser:

    REVENUE_KEYS = [
        "revenue",
        "total revenue",
        "revenue from operations",
        "income from operations",
        "total income",
    ]

    EBITDA_KEYS = [
        "ebitda",
        "operating ebitda",
        "earnings before interest tax depreciation",
    ]

    PAT_KEYS = [
        "pat",
        "profit after tax",
        "profit for the period",
        "net profit",
        "net income",
    ]

    EPS_KEYS = [
        "eps",
        "basic eps",
        "earnings per share",
    ]

    @staticmethod
    def normalize_key(
        value: Any,
    ) -> str:

        return (
            str(value)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        if isinstance(value, Decimal):
            return value

        try:

            text = (
                str(value)
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )

            return Decimal(text)

        except (
            InvalidOperation,
            ValueError,
        ):

            return None

    @classmethod
    def find_metric(
        cls,
        data: dict[str, Any],
        keys: list[str],
    ):

        normalized = {
            cls.normalize_key(k): v
            for k, v in data.items()
        }

        for key in keys:

            value = normalized.get(
                cls.normalize_key(key)
            )

            if value is not None:

                return cls.to_decimal(
                    value
                )

        return None

    @classmethod
    def parse(
        cls,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "revenue": cls.find_metric(
                data,
                cls.REVENUE_KEYS,
            ),
            "ebitda": cls.find_metric(
                data,
                cls.EBITDA_KEYS,
            ),
            "pat": cls.find_metric(
                data,
                cls.PAT_KEYS,
            ),
            "eps": cls.find_metric(
                data,
                cls.EPS_KEYS,
            ),
        }
