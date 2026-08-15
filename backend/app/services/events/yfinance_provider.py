from datetime import datetime, timezone

import yfinance as yf

from app.services.events.base import (
    EventProvider,
    MarketEvent,
)


class YFinanceEventProvider(
    EventProvider
):

    def _ticker_symbol(
        self,
        symbol: str,
    ) -> str:

        symbol = symbol.upper()

        if symbol.startswith("^"):
            return symbol

        if symbol.endswith(".NS"):
            return symbol

        return f"{symbol}.NS"

    # -------------------------------------------------
    # NEWS
    # -------------------------------------------------

    def _get_news(
        self,
        symbol: str,
        ticker,
    ) -> list[MarketEvent]:

        events = []

        try:
            news_items = ticker.news or []

        except Exception:
            return events

        for item in news_items:

            content = item.get(
                "content",
                {},
            )

            title = (
                content.get("title")
                or item.get("title")
            )

            if not title:
                continue

            publisher = (
                content.get("provider", {})
                .get("displayName")
            )

            canonical_url = (
                content.get(
                    "canonicalUrl",
                    {},
                )
                .get("url")
            )

            pub_date = (
                content.get("pubDate")
            )

            event_time = (
                self._parse_datetime(
                    pub_date
                )
                if pub_date
                else datetime.now(
                    timezone.utc
                )
            )

            event_key = (
                f"NEWS:{symbol}:"
                f"{canonical_url or title}"
            )

            events.append(
                MarketEvent(
                    symbol=symbol,
                    event_type="NEWS",
                    title=title,
                    description=(
                        content.get(
                            "summary"
                        )
                    ),
                    source=publisher
                    or "Yahoo Finance",
                    source_url=canonical_url,
                    event_key=event_key,
                    event_time=event_time,
                )
            )

        return events

    # -------------------------------------------------
    # DIVIDENDS
    # -------------------------------------------------

    def _get_dividends(
        self,
        symbol: str,
        ticker,
    ) -> list[MarketEvent]:

        events = []

        try:
            dividends = ticker.dividends

        except Exception:
            return events

        if dividends is None:
            return events

        # Only inspect recent entries.
        dividends = dividends.tail(10)

        for date, value in dividends.items():

            amount = float(value)

            event_time = (
                date.to_pydatetime()
                if hasattr(
                    date,
                    "to_pydatetime",
                )
                else datetime.now(
                    timezone.utc
                )
            )

            if event_time.tzinfo is None:
                event_time = event_time.replace(
                    tzinfo=timezone.utc
                )

            date_key = (
                event_time.date().isoformat()
            )

            event_key = (
                f"DIVIDEND:{symbol}:"
                f"{date_key}:{amount}"
            )

            events.append(
                MarketEvent(
                    symbol=symbol,
                    event_type="DIVIDEND",
                    title=(
                        f"{symbol} dividend "
                        f"of ₹{amount:.2f}"
                    ),
                    description=(
                        f"{symbol} recorded a "
                        f"dividend of "
                        f"₹{amount:.2f} per share."
                    ),
                    source="Yahoo Finance",
                    old_value=None,
                    new_value=amount,
                    event_key=event_key,
                    event_time=event_time,
                )
            )

        return events

    # -------------------------------------------------
    # STOCK SPLITS
    # -------------------------------------------------

    def _get_splits(
        self,
        symbol: str,
        ticker,
    ) -> list[MarketEvent]:

        events = []

        try:
            splits = ticker.splits

        except Exception:
            return events

        if splits is None:
            return events

        splits = splits.tail(10)

        for date, ratio in splits.items():

            ratio = float(ratio)

            event_time = (
                date.to_pydatetime()
                if hasattr(
                    date,
                    "to_pydatetime",
                )
                else datetime.now(
                    timezone.utc
                )
            )

            if event_time.tzinfo is None:
                event_time = event_time.replace(
                    tzinfo=timezone.utc
                )

            date_key = (
                event_time.date().isoformat()
            )

            event_key = (
                f"SPLIT:{symbol}:"
                f"{date_key}:{ratio}"
            )

            events.append(
                MarketEvent(
                    symbol=symbol,
                    event_type="SPLIT",
                    title=(
                        f"{symbol} stock split "
                        f"{ratio:g}:1"
                    ),
                    description=(
                        f"{symbol} recorded a "
                        f"stock split with "
                        f"ratio {ratio:g}:1."
                    ),
                    source="Yahoo Finance",
                    new_value=ratio,
                    event_key=event_key,
                    event_time=event_time,
                )
            )

        return events

    # -------------------------------------------------
    # ALL EVENTS
    # -------------------------------------------------

    def get_events(
        self,
        symbol: str,
    ) -> list[MarketEvent]:

        symbol = symbol.strip().upper()

        yahoo_symbol = self._ticker_symbol(
            symbol
        )

        ticker = yf.Ticker(
            yahoo_symbol
        )

        events = []

        events.extend(
            self._get_news(
                symbol,
                ticker,
            )
        )

        events.extend(
            self._get_dividends(
                symbol,
                ticker,
            )
        )

        events.extend(
            self._get_splits(
                symbol,
                ticker,
            )
        )

        return events

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime:

        if not value:
            return datetime.now(
                timezone.utc
            )

        try:

            parsed = datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed

        except ValueError:

            return datetime.now(
                timezone.utc
            )
