from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import re
import threading
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class MarketNewsItem:
    title: str
    url: str
    source: str
    published_at: datetime
    category: str
    importance: str


class MarketNewsService:
    """Fetch and cache high-signal Indian market news from public RSS feeds."""

    CACHE_TTL_SECONDS = 300
    FETCH_TIMEOUT_SECONDS = 5

    QUERIES = (
        (
            "Market",
            "Indian stock market Nifty Sensex stocks India",
        ),
        (
            "Macro",
            "India RBI inflation interest rates rupee economy markets",
        ),
        (
            "Corporate",
            "India stocks earnings results companies business markets",
        ),
        (
            "Flows & Commodities",
            "India FII DII crude oil gold markets stocks",
        ),
    )

    IMPORTANT_KEYWORDS = (
        "rbi",
        "rate cut",
        "rate hike",
        "inflation",
        "nifty",
        "sensex",
        "fii",
        "dii",
        "crude",
        "oil",
        "rupee",
        "tariff",
        "earnings",
        "results",
        "profit",
        "revenue",
        "ipo",
        "merger",
        "acquisition",
        "order",
        "guidance",
        "downgrade",
        "upgrade",
        "default",
        "fraud",
    )

    _cache: list[MarketNewsItem] | None = None
    _cache_expires_at: float = 0.0
    _cache_lock = threading.Lock()

    @classmethod
    def _rss_url(cls, query: str) -> str:
        return (
            "https://news.google.com/rss/search?"
            f"q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        )

    @staticmethod
    def _clean(value: str | None) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", " ", unescape(value)).strip()

    @classmethod
    def _importance(cls, title: str) -> str:
        lowered = title.lower()
        matches = sum(
            keyword in lowered
            for keyword in cls.IMPORTANT_KEYWORDS
        )

        if matches >= 2:
            return "HIGH"
        if matches == 1:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _parse_date(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        try:
            result = parsedate_to_datetime(value)
            if result.tzinfo is None:
                result = result.replace(
                    tzinfo=timezone.utc,
                )
            return result.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return datetime.now(timezone.utc)

    @classmethod
    def _fetch_query(
        cls,
        category: str,
        query: str,
    ) -> list[MarketNewsItem]:
        request = Request(
            cls._rss_url(query),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "Chrome/154.0 Safari/537.36"
                ),
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )

        with urlopen(
            request,
            timeout=cls.FETCH_TIMEOUT_SECONDS,
        ) as response:
            payload = response.read()

        root = ET.fromstring(payload)
        items: list[MarketNewsItem] = []

        for node in root.findall(".//item"):
            title = cls._clean(
                node.findtext("title"),
            )
            link = cls._clean(
                node.findtext("link"),
            )
            source = cls._clean(
                node.findtext("source"),
            )
            pub_date = cls._parse_date(
                node.findtext("pubDate"),
            )

            if not title or not link:
                continue

            items.append(
                MarketNewsItem(
                    title=title,
                    url=link,
                    source=source or "Google News",
                    published_at=pub_date,
                    category=category,
                    importance=cls._importance(title),
                )
            )

        return items[:10]

    @classmethod
    def get_latest(
        cls,
        limit: int = 12,
    ) -> list[MarketNewsItem]:
        now = datetime.now(timezone.utc).timestamp()

        with cls._cache_lock:
            if (
                cls._cache is not None
                and now < cls._cache_expires_at
            ):
                return cls._cache[:limit]

        collected: list[MarketNewsItem] = []

        with ThreadPoolExecutor(
            max_workers=len(cls.QUERIES),
            thread_name_prefix="market-news",
        ) as executor:
            futures = {
                executor.submit(
                    cls._fetch_query,
                    category,
                    query,
                ): category
                for category, query in cls.QUERIES
            }

            for future in as_completed(futures):
                try:
                    collected.extend(
                        future.result()
                    )
                except Exception:
                    continue

        # Deduplicate by normalized headline while keeping the newest version.
        unique: dict[str, MarketNewsItem] = {}

        for item in collected:
            key = re.sub(
                r"[^a-z0-9]+",
                " ",
                item.title.lower(),
            ).strip()

            existing = unique.get(key)
            if (
                existing is None
                or item.published_at > existing.published_at
            ):
                unique[key] = item

        ranked = sorted(
            unique.values(),
            key=lambda item: (
                item.importance != "HIGH",
                item.importance != "MEDIUM",
                -item.published_at.timestamp(),
            ),
        )

        ranked = ranked[:30]

        with cls._cache_lock:
            cls._cache = ranked
            cls._cache_expires_at = (
                datetime.now(timezone.utc).timestamp()
                + cls.CACHE_TTL_SECONDS
            )

        return ranked[:limit]
