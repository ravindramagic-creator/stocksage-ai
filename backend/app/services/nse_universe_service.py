from __future__ import annotations

import csv
import io
import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stock import Stock

logger = logging.getLogger("stocksage.nse_universe")


class NSEUniverseService:
    """Synchronize StockSage's stock master with NSE's official equity master."""

    EQUITY_URLS = (
        "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
        "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
    )

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/154.0 Safari/537.36"
                ),
                "Accept": "text/csv,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.nseindia.com/",
            }
        )

    def fetch_equity_master(self) -> list[dict[str, str]]:
        last_error: Exception | None = None

        for url in self.EQUITY_URLS:
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                text = response.content.decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                rows: list[dict[str, str]] = []

                for raw in reader:
                    row = {
                        str(key or "").strip().upper(): str(value or "").strip()
                        for key, value in raw.items()
                    }
                    symbol = row.get("SYMBOL", "").upper()
                    series = row.get("SERIES", "").upper()
                    company = row.get("NAME OF COMPANY", "").strip()

                    if not symbol or series not in {"EQ", "BE"} or not company:
                        continue

                    rows.append(
                        {
                            "symbol": symbol,
                            "company_name": company,
                            "series": series,
                        }
                    )

                if len(rows) < 1000:
                    raise ValueError(
                        f"NSE equity master returned only {len(rows)} equity rows"
                    )

                unique = {row["symbol"]: row for row in rows}
                result = list(unique.values())
                logger.info("Fetched %d NSE equity symbols", len(result))
                return result

            except Exception as exc:
                last_error = exc
                logger.warning("Unable to fetch NSE universe from %s: %s", url, exc)

        raise RuntimeError("Unable to download NSE equity master") from last_error

    def refresh_database(self, db: Session) -> int:
        # Download first. If NSE is unavailable, leave the last good snapshot intact.
        rows = self.fetch_equity_master()
        source_symbols = {row["symbol"] for row in rows}
        existing = {
            stock.symbol.upper(): stock
            for stock in db.scalars(select(Stock)).all()
        }

        # Preserve historical records, but keep delisted/removed symbols out of
        # the active screener universe without introducing a schema migration.
        for symbol, stock in existing.items():
            if stock.exchange == "NSE" and symbol not in source_symbols:
                stock.exchange = "NSEOLD"

        added = 0
        updated = 0

        for row in rows:
            symbol = row["symbol"]
            stock = existing.get(symbol)

            if stock is None:
                db.add(
                    Stock(
                        symbol=symbol,
                        company_name=row["company_name"],
                        exchange="NSE",
                        sector=None,
                    )
                )
                added += 1
                continue

            if stock.company_name != row["company_name"]:
                stock.company_name = row["company_name"]
                updated += 1

            if stock.exchange != "NSE":
                stock.exchange = "NSE"

        db.commit()

        logger.info(
            "NSE universe synchronized: source=%d added=%d updated=%d database=%d",
            len(rows),
            added,
            updated,
            len(existing) + added,
        )
        return len(rows)

    @staticmethod
    def database_count(db: Session) -> int:
        return int(db.query(Stock).filter(Stock.exchange == "NSE").count())
