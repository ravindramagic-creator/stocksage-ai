from __future__ import annotations

import time
from typing import Any

import yfinance as yf


class YahooFundamentalsProvider:
    """Rate-limited Yahoo fundamentals/history access for background jobs."""

    MIN_REQUEST_INTERVAL = 1.5
    COOLDOWN_SECONDS = 300

    def __init__(self):
        self._last_request = 0.0
        self._disabled_until = 0.0

    def _wait(self) -> None:
        now = time.monotonic()
        if now < self._disabled_until:
            raise RuntimeError("Yahoo fundamentals provider is temporarily cooling down")
        delay = self.MIN_REQUEST_INTERVAL - (now - self._last_request)
        if delay > 0:
            time.sleep(delay)
        self._last_request = time.monotonic()

    def get_snapshot_data(self, symbol: str) -> dict[str, Any]:
        self._wait()
        try:
            ticker = yf.Ticker(f"{symbol.upper()}.NS")
            info = ticker.info or {}

            # ROCE is not reliably exposed by Yahoo as a standard field.
            # Fetch the financial statements so the service can calculate
            # EBIT / capital employed instead of incorrectly using ROA.
            financials = {}
            balance_sheet = {}

            try:
                financials = ticker.financials
            except Exception:
                pass

            try:
                balance_sheet = ticker.balance_sheet
            except Exception:
                pass

            self._last_request = time.monotonic()
            return {
                "info": info,
                "financials": financials,
                "balance_sheet": balance_sheet,
            }
        except Exception as exc:
            text = str(exc).lower()
            if (
                "too many requests" in text
                or exc.__class__.__name__ == "YFRateLimitError"
            ):
                self._disabled_until = time.monotonic() + self.COOLDOWN_SECONDS
            raise

    def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ):
        self._wait()
        try:
            ticker = yf.Ticker(f"{symbol.upper()}.NS")
            history = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=False,
            )
            self._last_request = time.monotonic()
            return history
        except Exception as exc:
            text = str(exc).lower()
            if (
                "too many requests" in text
                or exc.__class__.__name__ == "YFRateLimitError"
            ):
                self._disabled_until = time.monotonic() + self.COOLDOWN_SECONDS
            raise
