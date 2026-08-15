from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests

from app.services.events.base import (
    EventProvider,
    MarketEvent,
)


logger = logging.getLogger(
    "stocksage.nse_provider"
)


class NSEEventProvider(EventProvider):

    BASE_URL = "https://www.nseindia.com"

    ANNOUNCEMENTS_URL = (
        "https://www.nseindia.com/"
        "api/corporate-announcements"
    )

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/150.0 Safari/537.36"
            ),
            "Accept": (
                "application/json,text/plain,*/*"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
            "Referer": (
                "https://www.nseindia.com/"
            ),
        })

    # -------------------------------------------------
    # NSE SESSION
    # -------------------------------------------------

    def _initialize_session(self) -> None:

        try:

            response = self.session.get(
                self.BASE_URL,
                timeout=10,
            )

            response.raise_for_status()

        except requests.RequestException:

            logger.warning(
                "Unable to initialize NSE session"
            )

    # -------------------------------------------------
    # HTTP GET
    # -------------------------------------------------

    def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> Any:

        self._initialize_session()

        response = self.session.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    # -------------------------------------------------
    # SYMBOL
    # -------------------------------------------------

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:

        symbol = symbol.strip().upper()

        if symbol.endswith(".NS"):
            symbol = symbol[:-3]

        return symbol

    # -------------------------------------------------
    # CORPORATE ANNOUNCEMENTS
    # -------------------------------------------------

    def get_announcements(
        self,
        symbol: str,
    ) -> list[MarketEvent]:

        symbol = self._normalize_symbol(
            symbol
        )

        try:

            data = self._get(
                self.ANNOUNCEMENTS_URL,
                params={
                    "index": "equities",
                    "symbol": symbol,
                },
            )

        except requests.RequestException as exc:

            logger.warning(
                "NSE announcement request failed "
                "for %s: %s",
                symbol,
                exc,
            )

            return []

        except Exception:

            logger.exception(
                "Unexpected NSE announcement error "
                "for %s",
                symbol,
            )

            return []

        if not isinstance(data, list):
            logger.warning(
                "Unexpected NSE announcement response "
                "for %s: %s",
                symbol,
                type(data),
            )
            return []

        events: list[MarketEvent] = []

        for item in data:

            if not isinstance(item, dict):
                continue

            event = self._announcement_to_event(
                symbol,
                item,
            )

            if event:
                events.append(event)

        return events

    # -------------------------------------------------
    # CONVERT ANNOUNCEMENT
    # -------------------------------------------------

    def _announcement_to_event(
        self,
        symbol: str,
        item: dict[str, Any],
    ) -> MarketEvent | None:

        subject = (
            item.get("subject")
            or item.get("desc")
            or item.get("description")
        )

        if not subject:
            return None

        subject = str(subject).strip()

        broadcast_date = (
            item.get("broadcastDate")
            or item.get("date")
            or item.get("an_dt")
        )

        event_time = self._parse_datetime(
            broadcast_date
        )

        event_type = self._classify_subject(
            subject
        )

        document_url = (
            item.get("attchmntFile")
            or item.get("attachment")
            or item.get("fileUrl")
        )

        event_key = (
            f"NSE:{symbol}:"
            f"{event_type}:"
            f"{broadcast_date}:"
            f"{subject}"
        )

        return MarketEvent(
            symbol=symbol,
            event_type=event_type,
            title=f"{symbol}: {subject}",
            description=(
                f"NSE corporate announcement: "
                f"{subject}"
            ),
            source="NSE India",
            source_url=document_url,
            event_key=event_key,
            event_time=event_time,
        )

    # -------------------------------------------------
    # CLASSIFY ANNOUNCEMENT
    # -------------------------------------------------

    @staticmethod
    def _classify_subject(
        subject: str,
    ) -> str:

        text = subject.lower()

        if any(
            word in text
            for word in [
                "financial results",
                "financial result",
                "quarterly results",
                "result",
            ]
        ):
            return "RESULT"

        if any(
            word in text
            for word in [
                "bagging",
                "order",
                "contract",
                "received order",
                "work order",
            ]
        ):
            return "ORDER"

        if any(
            word in text
            for word in [
                "board meeting",
                "board of directors",
            ]
        ):
            return "BOARD_MEETING"

        if "dividend" in text:
            return "DIVIDEND"

        if "split" in text:
            return "SPLIT"

        if "bonus" in text:
            return "BONUS"

        if "acquisition" in text:
            return "ACQUISITION"

        if "press release" in text:
            return "PRESS_RELEASE"

        return "CORPORATE"

    # -------------------------------------------------
    # DATETIME
    # -------------------------------------------------

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:

        if isinstance(value, datetime):

            if value.tzinfo is None:
                return value.replace(
                    tzinfo=timezone.utc
                )

            return value

        if not value:

            return datetime.now(
                timezone.utc
            )

        text = str(value).strip()

        formats = [
            "%d-%b-%Y %H:%M:%S",
            "%d-%b-%Y %H:%M",
            "%d-%b-%Y",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
        ]

        for fmt in formats:

            try:

                return datetime.strptime(
                    text,
                    fmt,
                ).replace(
                    tzinfo=timezone.utc
                )

            except ValueError:
                continue

        return datetime.now(
            timezone.utc
        )

    # -------------------------------------------------
    # PROVIDER ENTRY POINT
    # -------------------------------------------------

    def get_events(
        self,
        symbol: str,
    ) -> list[MarketEvent]:

        symbol = self._normalize_symbol(
            symbol
        )

        # IMPORTANT:
        #
        # Do NOT call get_results() here.
        #
        # The old /api/corporate-financial-results
        # endpoint is returning HTTP 404.
        #
        # Financial-result announcements will be
        # picked up when NSE publishes them through
        # the corporate-announcements feed.

        return self.get_announcements(
            symbol
        )
