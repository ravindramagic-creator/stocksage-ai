from __future__ import annotations

import logging
import re
import time
from datetime import date, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from app.providers.auto_sales_provider import AutoSalesProvider

logger = logging.getLogger("stocksage.auto_sales_provider")


class VahanRetailProvider(AutoSalesProvider):
    """Fetch monthly OEM registration data from a Vahan-derived public page.

    These values represent vehicle registrations/retail activity, not OEM
    wholesale dispatches. The source page is maintained separately from
    StockSage-AI and its HTML can change, so parsing is intentionally tolerant.
    """

    BASE_URL = "https://indianstockalerts.com/vahan"

    SEGMENTS = {
        "PV": "pv",
        "2W": "2w",
        "3W": "3w",
        "CV": "cv",
        "TRACTOR": "tractor",
    }

    SYMBOLS = {
        "MARUTI": "MARUTI",
        "TATA": "TATAMOTORS",
        "MAHINDRA": "M&M",
        "HYUNDAI": "HYUNDAI",
        "TOYOTA": "TOYOTA",
        "KIA": "KIA",
        "HERO": "HEROMOTOCO",
        "HONDA": "HONDA",
        "TVS": "TVSMOTOR",
        "BAJAJ": "BAJAJ-AUTO",
        "SUZUKI": "SUZUKI",
        "ROYAL ENFIELD": "EICHERMOT",
        "EICHER": "EICHERMOT",
        "YAMAHA": "YAMAHA",
        "ATHER": "ATHERENERGY",
        "OLA": "OLAELEC",
        "ASHOK": "ASHOKLEY",
        "VECV": "EICHERMOT",
        "FORCE": "FORCEMOT",
    }

    def __init__(self, timeout: int = 20, retries: int = 3):
        self.timeout = timeout
        self.retries = retries

    def fetch_month(self, month: date) -> list[dict]:
        records: list[dict] = []
        for segment, slug in self.SEGMENTS.items():
            try:
                records.extend(self._fetch_segment(slug, segment, month))
            except Exception:
                logger.exception("Auto-sales segment fetch failed: %s", segment)
        return records

    def fetch_history(self, segment: str | None = None) -> list[dict]:
        records: list[dict] = []
        if segment:
            key = segment.upper()
            segments = {key: self.SEGMENTS[key]} if key in self.SEGMENTS else {}
        else:
            segments = self.SEGMENTS

        for segment_name, slug in segments.items():
            try:
                segment_records = self._fetch_segment(slug, segment_name, None)
                records.extend(segment_records)
                logger.info(
                    "Fetched %d auto-sales records for %s",
                    len(segment_records),
                    segment_name,
                )
            except Exception:
                # A single broken segment/source must not prevent the other
                # segments from being refreshed.
                logger.exception("Auto-sales segment fetch failed: %s", segment_name)

        return records

    def _download(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) StockSage-AI/1.0",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-IN,en;q=0.9",
                        "Cache-Control": "no-cache",
                    },
                )
                with urlopen(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", 200)
                    if status != 200:
                        raise RuntimeError(f"HTTP {status} from {url}")
                    return response.read().decode("utf-8", errors="replace")
            except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(attempt)

        raise RuntimeError(f"Unable to fetch auto-sales source: {url}: {last_error}")

    def _fetch_segment(
        self,
        slug: str,
        segment: str,
        requested_month: date | None,
    ) -> list[dict]:
        url = f"{self.BASE_URL}/{slug}"
        html = self._download(url)
        soup = BeautifulSoup(html, "html.parser")
        table = self._find_monthly_table(soup)
        if table is None:
            raise RuntimeError(f"Monthly auto-sales table not found: {url}")

        company_names = self._extract_company_headers(table)
        if not company_names:
            raise RuntimeError(f"OEM headers not found: {url}")

        result: list[dict] = []
        for row in table.find_all("tr"):
            cells = [
                self._clean(cell.get_text(" ", strip=True))
                for cell in row.find_all(["td", "th"])
            ]
            if not cells:
                continue

            month_value = self._parse_month(cells[0])
            if month_value is None:
                continue
            if requested_month and month_value != requested_month.replace(day=1):
                continue

            # Every company contributes Vol / YoY / MS. Any final Industry
            # group is deliberately ignored.
            data_cells = cells[1:]
            for index, company_name in enumerate(company_names):
                start = index * 3
                if start + 2 >= len(data_cells):
                    break

                volume = self._parse_number(data_cells[start])
                yoy = self._parse_percent(data_cells[start + 1])
                share = self._parse_percent(data_cells[start + 2])
                if volume is None:
                    continue

                result.append(
                    {
                        "symbol": self._symbol_for(company_name),
                        "company_name": company_name,
                        "segment": segment,
                        "month": month_value,
                        "registrations": volume,
                        "total_sales": volume,
                        "yoy_growth": yoy,
                        "market_share": share,
                        "data_type": "REGISTRATION",
                        "source": "VAHAN_DERIVED",
                        "source_url": url,
                        "is_projected": "(P)" in cells[0] or "*" in cells[0],
                    }
                )

        return result

    @staticmethod
    def _find_monthly_table(soup: BeautifulSoup):
        """Find the data table without relying on exact page wording."""
        candidates = []
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True).lower()
            if "month" in text and "industry" in text:
                score = 0
                for token in ("maruti", "tata", "mahindra", "hyundai", "hero", "honda", "tvs"):
                    if token in text:
                        score += 1
                if "yoy" in text:
                    score += 2
                candidates.append((score, table))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _extract_company_headers(self, table: BeautifulSoup) -> list[str]:
        """Extract OEM names from the table header even if th/td markup changes."""
        rows = table.find_all("tr")[:5]
        metric_names = {"month", "vol", "yoy", "ms", "industry", "volume", "market share"}

        for row in rows:
            cells = row.find_all(["th", "td"])
            names: list[str] = []
            for cell in cells:
                text = self._clean(cell.get_text(" ", strip=True))
                lower = text.lower()
                if not text or lower in metric_names:
                    continue
                if lower.startswith("sep-") or lower.startswith("aug-"):
                    continue
                if re.fullmatch(r"[+-]?\d+(?:\.\d+)?%?", text):
                    continue
                if text in {"Vol", "YoY", "MS"}:
                    continue
                colspan = int(cell.get("colspan", 1) or 1)
                # A company header normally spans three metrics. If colspan is
                # absent, known OEM names still allow us to recognize it.
                is_known = any(key in lower for key in self.SYMBOLS)
                if colspan >= 2 or is_known:
                    if lower != "industry" and text not in names:
                        names.append(text)

            if names:
                # Never treat the final Industry aggregate as an OEM.
                return [name for name in names if name.lower() != "industry"]

        return []

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _parse_month(value: str) -> date | None:
        value = value.replace("(P)", "").replace("*", "").strip()
        for fmt in ("%b-%y", "%B-%Y", "%b-%Y", "%B-%y"):
            try:
                return datetime.strptime(value, fmt).date().replace(day=1)
            except ValueError:
                pass
        return None

    @staticmethod
    def _parse_number(value: str) -> int | None:
        value = value.replace(",", "").strip().upper()
        if not value or value in {"—", "-", "NA", "N/A"}:
            return None
        multiplier = 1
        if value.endswith("K"):
            multiplier = 1_000
            value = value[:-1]
        elif value.endswith("M"):
            multiplier = 1_000_000
            value = value[:-1]
        try:
            return round(float(value) * multiplier)
        except ValueError:
            return None

    @staticmethod
    def _parse_percent(value: str) -> float | None:
        value = value.replace("%", "").replace(",", "").strip()
        if not value or value in {"—", "-", "NA", "N/A"}:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _symbol_for(self, company_name: str) -> str:
        normalized = company_name.upper().strip()
        for key, symbol in self.SYMBOLS.items():
            if key in normalized:
                return symbol
        return normalized.replace(" ", "_")
