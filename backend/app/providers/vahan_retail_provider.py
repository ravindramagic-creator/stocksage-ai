from __future__ import annotations

import re
from datetime import date, datetime
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from app.providers.auto_sales_provider import AutoSalesProvider


class VahanRetailProvider(AutoSalesProvider):
    """Parse monthly OEM registration data derived from VAHAN.

    The source is a public Vahan-derived dashboard. These are registrations
    (retail), not manufacturer wholesale/dispatch sales.
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

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def fetch_month(self, month: date) -> list[dict]:
        # The source pages expose an archive table containing historical
        # monthly rows, so one request per segment gives the full history.
        records: list[dict] = []
        for segment, slug in self.SEGMENTS.items():
            records.extend(self._fetch_segment(slug, segment, month))
        return records

    def fetch_history(self, segment: str | None = None) -> list[dict]:
        records: list[dict] = []
        segments = (
            {segment.upper(): self.SEGMENTS[segment.upper()]}
            if segment and segment.upper() in self.SEGMENTS
            else self.SEGMENTS
        )
        for segment_name, slug in segments.items():
            records.extend(self._fetch_segment(slug, segment_name, None))
        return records

    def _fetch_segment(
        self,
        slug: str,
        segment: str,
        requested_month: date | None,
    ) -> list[dict]:
        url = f"{self.BASE_URL}/{slug}"
        request = Request(
            url,
            headers={
                "User-Agent": "StockSage-AI/1.0 (+monthly-auto-sales)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        with urlopen(request, timeout=self.timeout) as response:
            html = response.read().decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "html.parser")
        table = self._find_monthly_table(soup)
        if table is None:
            raise RuntimeError(f"Monthly auto-sales table not found: {url}")

        company_names = self._extract_company_headers(table)
        if not company_names:
            raise RuntimeError(f"OEM headers not found: {url}")

        result: list[dict] = []
        for row in table.find_all("tr"):
            cells = [self._clean(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])]
            if not cells:
                continue

            month_value = self._parse_month(cells[0])
            if month_value is None:
                continue
            if requested_month and month_value != requested_month.replace(day=1):
                continue

            # Each OEM contributes Vol / YoY / MS. The last Industry group
            # is intentionally ignored.
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
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True).lower()
            if "monthly" in text and "industry" in text and "yoy" in text:
                return table
        return None

    @staticmethod
    def _extract_company_headers(table: BeautifulSoup) -> list[str]:
        rows = table.find_all("tr")[:3]
        if not rows:
            return []

        for row in rows:
            headers = row.find_all("th")
            names: list[str] = []
            for header in headers:
                text = header.get_text(" ", strip=True)
                colspan = int(header.get("colspan", 1) or 1)
                if text and text.lower() not in {"month", "industry"}:
                    # Company headers normally span three metric columns.
                    names.append(text)
                elif text.lower() == "industry":
                    break
                elif colspan > 1 and text:
                    names.append(text)
            if names:
                return names
        return []

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _parse_month(value: str) -> date | None:
        value = value.replace("(P)", "").replace("*", "").strip()
        for fmt in ("%b-%y", "%B-%Y"):
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
