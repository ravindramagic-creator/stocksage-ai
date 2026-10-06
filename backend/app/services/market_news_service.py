from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
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
    """Fetch fresh, stock-specific Indian market news."""

    CACHE_TTL_SECONDS = 300
    FETCH_TIMEOUT_SECONDS = 5
    INDIA_TZ = ZoneInfo("Asia/Kolkata")

    # Keep the feed focused on listed companies and tradeable stock events.
    # Macro-only headlines are intentionally excluded from this dashboard.
    QUERIES = (
        (
            "Stock Moves",
            "Indian stocks shares today NSE BSE stock price gain fall company",
        ),
        (
            "Earnings & Results",
            "India listed companies earnings results revenue profit EPS stocks NSE BSE",
        ),
        (
            "Corporate Actions",
            "Indian stocks dividend bonus split buyback merger acquisition order stake pledge NSE BSE",
        ),
        (
            "Brokerage & Ratings",
            "Indian stocks brokerage upgrade downgrade target price buy sell rating NSE BSE",
        ),
        (
            "IPO & New Listings",
            "India IPO listing shares stock market NSE BSE company IPO today",
        ),
    )

    STOCK_KEYWORDS = (
        "stock",
        "stocks",
        "share",
        "shares",
        "nse",
        "bse",
        "listed",
        "company",
        "earnings",
        "results",
        "revenue",
        "profit",
        "eps",
        "ebitda",
        "order",
        "contract",
        "dividend",
        "bonus",
        "split",
        "buyback",
        "merger",
        "acquisition",
        "stake",
        "pledge",
        "ipo",
        "listing",
        "target price",
        "price target",
        "upgrade",
        "downgrade",
        "buy rating",
        "sell rating",
        "block deal",
        "bulk deal",
        "promoter",
        "fund raising",
        "fundraise",
        "capacity",
        "guidance",
    )

    HIGH_IMPACT_KEYWORDS = (
        "results",
        "earnings",
        "profit",
        "revenue",
        "order",
        "contract",
        "acquisition",
        "merger",
        "buyback",
        "dividend",
        "bonus",
        "split",
        "upgrade",
        "downgrade",
        "target price",
        "block deal",
        "bulk deal",
        "promoter",
        "fund raising",
        "fundraise",
        "fraud",
        "default",
    )

    _cache: list[MarketNewsItem] | None = None
    _cache_expires_at: float = 0.0
    _cache_lock = threading.Lock()

    @classmethod
    def _news_window(
        cls,
    ) -> tuple[datetime, datetime]:
        now_ist = datetime.now(
            timezone.utc,
        ).astimezone(cls.INDIA_TZ)

        today_start = now_ist.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        start = today_start - timedelta(days=1)

        return (
            start.astimezone(timezone.utc),
            now_ist.astimezone(timezone.utc),
        )

    @classmethod
    def _rss_url(cls, query: str) -> str:
        query = f"{query} when:2d"
        return (
            "https://news.google.com/rss/search?"
            f"q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        )

    @staticmethod
    def _clean(value: str | None) -> str:
        if not value:
            return ""
        return re.sub(
            r"\s+",
            " ",
            unescape(value),
        ).strip()

    @classmethod
    def _stock_relevance(cls, title: str) -> int:
        lowered = title.lower()
        return sum(
            1
            for keyword in cls.STOCK_KEYWORDS
            if keyword in lowered
        )

    @classmethod
    def _importance(
        cls,
        title: str,
    ) -> str:
        lowered = title.lower()
        matches = sum(
            keyword in lowered
            for keyword in cls.HIGH_IMPACT_KEYWORDS
        )

        if matches >= 2:
            return "HIGH"
        if matches == 1:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _parse_date(
        value: str | None,
    ) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        try:
            result = parsedate_to_datetime(value)

            if result.tzinfo is None:
                result = result.replace(
                    tzinfo=timezone.utc,
                )

            return result.astimezone(timezone.utc)
        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
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
                    "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
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
        start_utc, end_utc = cls._news_window()
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

            if pub_date < start_utc or pub_date > end_utc:
                continue

            # Relevance threshold prevents generic macro headlines from
            # leaking into the stock-news dashboard.
            relevance = cls._stock_relevance(title)
            if relevance < 1:
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

        return items[:20]

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
            thread_name_prefix="stock-news",
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

        # Prioritize high-impact stock events, then freshness.
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
