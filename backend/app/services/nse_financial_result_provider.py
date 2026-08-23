from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urljoin
import re
import xml.etree.ElementTree as ET

import requests


class NSEFinancialResultProvider:
    """
    NSE financial result provider.

    Data sources:

    1. Legacy NSE results-comparison API
       ----------------------------------
       /api/results-comparision

       Used for older historical quarters.

    2. NSE Integrated Filing - Financials
       -----------------------------------
       /api/integrated-filing-results

       Used for current filings.

       The Integrated Filing catalog provides an XBRL URL.
       We download the XBRL and extract the actual financial facts.

    XBRL namespaces supported:

        in-capmkt
        in-bse-fin
        in-ind-as

    Main normalized fields:

        revenue
        pat
        eps
        ebitda
        period_from
        period_ended
        consolidated
    """

    BASE_URL = "https://www.nseindia.com"

    RESULTS_COMPARISON_URL = (
        f"{BASE_URL}/api/results-comparision"
    )

    INTEGRATED_FILINGS_URL = (
        f"{BASE_URL}/api/integrated-filing-results"
    )

    LEGACY_FINANCIAL_FILINGS_URL = (
        f"{BASE_URL}/api/corporates-financial-results"
    )

    WEBSITE_URL = (
        f"{BASE_URL}/companies-listing/"
        "corporate-filings-financial-results"
    )

    INTEGRATED_WEBSITE_URL = (
        f"{BASE_URL}/companies-listing/"
        "corporate-integrated-filing"
    )

    def __init__(
        self,
        timeout: int = 30,
    ) -> None:

        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "application/json,"
                    "text/plain,*/*"
                ),
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
                "Referer": (
                    f"{self.BASE_URL}/"
                ),
                "Connection": "keep-alive",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        self._bootstrapped = False

    # ============================================================
    # Session bootstrap
    # ============================================================

    def _bootstrap(self) -> None:

        if self._bootstrapped:
            return

        response = self.session.get(
            self.BASE_URL,
            timeout=self.timeout,
        )

        response.raise_for_status()

        self._bootstrapped = True

    # ============================================================
    # Generic GET
    # ============================================================

    def _get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> Any:

        self._bootstrap()

        response = self.session.get(
            url,
            params=params or {},
            timeout=self.timeout,
        )

        if response.status_code in (
            401,
            403,
        ):

            self._bootstrapped = False

            self.session.cookies.clear()

            self._bootstrap()

            response = self.session.get(
                url,
                params=params or {},
                timeout=self.timeout,
            )

        response.raise_for_status()

        return response.json()

    # ============================================================
    # Generic binary/text download
    # ============================================================

    def _download(
        self,
        url: str,
    ) -> bytes:

        self._bootstrap()

        response = self.session.get(
            url,
            timeout=self.timeout,
            headers={
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml,"
                    "text/xml,*/*"
                )
            },
        )

        if response.status_code in (
            401,
            403,
        ):

            self._bootstrapped = False

            self.session.cookies.clear()

            self._bootstrap()

            response = self.session.get(
                url,
                timeout=self.timeout,
            )

        response.raise_for_status()

        return response.content

    # ============================================================
    # Conversion helpers
    # ============================================================

    @staticmethod
    def to_decimal(
        value: Any,
    ) -> Decimal | None:

        if value is None:
            return None

        if isinstance(value, Decimal):
            return value

        try:

            text = str(value).strip()

            if not text:
                return None

            text = (
                text
                .replace(",", "")
                .replace("₹", "")
            )

            return Decimal(text)

        except Exception:

            return None

    @staticmethod
    def to_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        text = str(value).strip()

        formats = (
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d %b %Y",
            "%d %B %Y",
        )

        for fmt in formats:

            try:

                return datetime.strptime(
                    text,
                    fmt,
                ).date()

            except ValueError:
                continue

        # ISO timestamp

        try:

            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).date()

        except Exception:
            pass

        return None

    @staticmethod
    def normalize_url(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        return urljoin(
            "https://www.nseindia.com",
            text,
        )

    @staticmethod
    def normalize_key(
        value: Any,
    ) -> str:

        text = str(value or "")

        text = re.sub(
            r"[^a-zA-Z0-9]+",
            "",
            text,
        )

        return text.lower()

    # ============================================================
    # Results comparison
    # ============================================================

    def get_results_comparison(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        data = self._get(
            self.RESULTS_COMPARISON_URL,
            {
                "symbol": symbol,
            },
        )

        if not isinstance(data, dict):
            return []

        rows = data.get(
            "resCmpData",
            [],
        )

        if not isinstance(rows, list):
            return []

        return rows

    # ============================================================
    # Integrated filing catalog
    # ============================================================

    def get_integrated_filings(
        self,
        symbol: str,
        size: int = 100,
    ) -> list[dict[str, Any]]:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        all_rows: list[dict[str, Any]] = []

        page = 1

        while True:

            data = self._get(
                self.INTEGRATED_FILINGS_URL,
                {
                    "type": (
                        "Integrated Filing- Financials"
                    ),
                    "page": page,
                    "size": size,
                    "index": "equities",
                    "symbol": symbol,
                },
            )

            rows: list[dict[str, Any]] = []

            if isinstance(data, list):

                rows = [
                    x
                    for x in data
                    if isinstance(x, dict)
                ]

            elif isinstance(data, dict):

                for key in (
                    "data",
                    "results",
                    "result",
                    "records",
                    "items",
                ):

                    candidate = data.get(key)

                    if isinstance(candidate, list):

                        rows = [
                            x
                            for x in candidate
                            if isinstance(x, dict)
                        ]

                        break

            if not rows:
                break

            all_rows.extend(rows)

            # Most NSE responses provide total count.
            total = None

            if isinstance(data, dict):

                for key in (
                    "total",
                    "totalRecords",
                    "totalCount",
                    "recordsTotal",
                ):

                    value = data.get(key)

                    if value is not None:

                        try:
                            total = int(value)
                        except Exception:
                            total = None

                        break

            if total is not None:

                if len(all_rows) >= total:
                    break

            if len(rows) < size:
                break

            page += 1

            # Safety guard.
            if page > 20:
                break

        return all_rows

    # ============================================================
    # Compatibility method
    #
    # Existing code calls:
    #
    # get_financial_result_filings()
    #
    # Keep this method so we don't have to change callers.
    # ============================================================

    def get_financial_result_filings(
        self,
        symbol: str,
    ) -> list[dict[str, Any]]:

        return self.get_integrated_filings(
            symbol,
            size=100,
        )

    # ============================================================
    # Find value recursively
    # ============================================================

    @classmethod
    def _find_value(
        cls,
        obj: Any,
        keys: tuple[str, ...],
    ) -> Any:

        wanted = {
            cls.normalize_key(key)
            for key in keys
        }

        if isinstance(obj, dict):

            for key, value in obj.items():

                if (
                    cls.normalize_key(key)
                    in wanted
                ):
                    return value

            for value in obj.values():

                found = cls._find_value(
                    value,
                    keys,
                )

                if found is not None:
                    return found

        elif isinstance(obj, list):

            for item in obj:

                found = cls._find_value(
                    item,
                    keys,
                )

                if found is not None:
                    return found

        return None

    # ============================================================
    # Extract filing metadata
    # ============================================================

    def _filing_symbol(
        self,
        row: dict[str, Any],
    ) -> str | None:

        value = self._find_value(
            row,
            (
                "symbol",
                "Symbol",
                "sm_symbol",
            ),
        )

        return (
            str(value).strip().upper()
            if value is not None
            else None
        )

    def _filing_period_end(
        self,
        row: dict[str, Any],
    ) -> date | None:

        value = self._find_value(
            row,
            (
                "quarterEndDate",
                "quarter end date",
                "periodEnded",
                "period_ended",
                "periodEndDate",
                "toDate",
                "to_dt",
                "endDate",
            ),
        )

        return self.to_date(value)

    def _filing_company_name(
        self,
        row: dict[str, Any],
    ) -> str | None:

        value = self._find_value(
            row,
            (
                "companyName",
                "company_name",
                "issuer",
                "company",
            ),
        )

        if value is None:
            return None

        return str(value).strip()

    def _filing_xbrl_url(
        self,
        row: dict[str, Any],
    ) -> str | None:

        value = self._find_value(
            row,
            (
                "xbrl",
                "xbrlFile",
                "xbrlFileLink",
                "xbrlUrl",
                "xbrlURL",
                "xbrlLink",
                "xbrl_file",
            ),
        )

        return self.normalize_url(value)

    def _filing_broadcast_date(
        self,
        row: dict[str, Any],
    ) -> datetime | None:

        value = self._find_value(
            row,
            (
                "broadcastDateTime",
                "broadcast date time",
                "broadcastDate",
                "broadcast_date",
                "broadcastTime",
            ),
        )

        if value is None:
            return None

        text = str(value).strip()

        formats = (
            "%d-%b-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d-%b-%Y %H:%M",
            "%d-%m-%Y %H:%M",
        )

        for fmt in formats:

            try:

                return datetime.strptime(
                    text,
                    fmt,
                )

            except ValueError:
                continue

        try:

            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

        except Exception:
            return None

    def _filing_consolidated(
        self,
        row: dict[str, Any],
    ) -> bool:

        value = self._find_value(
            row,
            (
                "consolidated",
                "consolidatedStandalone",
                "consolidatedOrStandalone",
                "natureOfReport",
                "natureOfReportStandaloneConsolidated",
                "reportType",
            ),
        )

        if value is None:
            return True

        text = str(value).strip().lower()

        if "standalone" in text:
            return False

        if "consolidated" in text:
            return True

        return True

    # ============================================================
    # XBRL helpers
    # ============================================================

    @staticmethod
    def _local_name(
        tag: str,
    ) -> str:

        if "}" in tag:
            tag = tag.rsplit(
                "}",
                1,
            )[1]

        if ":" in tag:
            tag = tag.rsplit(
                ":",
                1,
            )[1]

        return tag

    @classmethod
    def _tag_name(
        cls,
        element: ET.Element,
    ) -> str:

        return cls._local_name(
            element.tag
        )

    @classmethod
    def _context_nodes(
        cls,
        root: ET.Element,
    ) -> dict[str, ET.Element]:

        contexts: dict[
            str,
            ET.Element,
        ] = {}

        for element in root.iter():

            if (
                cls._local_name(
                    element.tag
                ).lower()
                == "context"
            ):

                context_id = (
                    element.attrib.get("id")
                )

                if context_id:
                    contexts[
                        context_id
                    ] = element

        return contexts

    @classmethod
    def _context_period(
        cls,
        context: ET.Element,
    ) -> tuple[
        date | None,
        date | None,
    ]:

        start = None
        end = None

        for element in context.iter():

            name = cls._local_name(
                element.tag
            ).lower()

            text = (
                element.text.strip()
                if element.text
                else ""
            )

            if name == "startdate":
                start = cls.to_date(text)

            elif name == "enddate":
                end = cls.to_date(text)

            elif name == "instant":

                instant = cls.to_date(text)

                if instant:
                    start = instant
                    end = instant

        return start, end

    @classmethod
    def _context_dimension_text(
        cls,
        context: ET.Element,
    ) -> str:

        values: list[str] = []

        for element in context.iter():

            name = cls._local_name(
                element.tag
            ).lower()

            if name in (
                "explicitmember",
                "typedmember",
            ):

                text = (
                    "".join(
                        element.itertext()
                    ).strip()
                )

                if text:
                    values.append(text)

        return " ".join(values).lower()

    @classmethod
    def _is_consolidated_context(
        cls,
        context: ET.Element,
    ) -> bool:

        text = (
            cls._context_dimension_text(
                context
            )
        )

        if not text:
            return True

        if "standalone" in text:
            return False

        if "consolidated" in text:
            return True

        # Common XBRL dimension values.
        if (
            "consolidated" in text
            or "group" in text
        ):
            return True

        return True

    @classmethod
    def _context_score(
        cls,
        context: ET.Element,
        period_end: date | None,
    ) -> int:

        score = 0

        start, end = cls._context_period(
            context
        )

        if (
            period_end is not None
            and end == period_end
        ):
            score += 100

        dimension_text = (
            cls._context_dimension_text(
                context
            )
        )

        if not dimension_text:
            score += 50

        if "oned" in dimension_text:
            score += 30

        if "fourd" in dimension_text:
            score -= 20

        return score

    @classmethod
    def _parse_xbrl(
        cls,
        xml_data: bytes,
        period_end: date | None = None,
        consolidated: bool = True,
    ) -> dict[str, Any]:

        # --------------------------------------------------------
        # Some NSE XBRL links occasionally return HTML.
        # ET will still parse valid XHTML.
        # --------------------------------------------------------

        root = ET.fromstring(
            xml_data
        )

        contexts = cls._context_nodes(
            root
        )

        facts: list[
            tuple[
                ET.Element,
                str,
                Decimal | None,
            ]
        ] = []

        for element in root.iter():

            if len(element):
                continue

            name = cls._tag_name(
                element
            )

            if not name:
                continue

            text = (
                element.text.strip()
                if element.text
                else ""
            )

            if not text:
                continue

            numeric = cls.to_decimal(
                text
            )

            if numeric is None:
                continue

            context_ref = (
                element.attrib.get(
                    "contextRef"
                )
            )

            if not context_ref:
                continue

            facts.append(
                (
                    element,
                    name.lower(),
                    numeric,
                )
            )

        # --------------------------------------------------------
        # Context candidates
        # --------------------------------------------------------

        context_candidates: list[
            tuple[
                int,
                str,
                date | None,
                date | None,
            ]
        ] = []

        for context_id, context in contexts.items():

            start, end = (
                cls._context_period(
                    context
                )
            )

            if end is None:
                continue

            is_consolidated_context = (
                cls._is_consolidated_context(
                    context
                )
            )

            if (
                consolidated
                and not is_consolidated_context
            ):
                continue

            if (
                not consolidated
                and is_consolidated_context
            ):
                continue

            score = cls._context_score(
                context,
                period_end,
            )

            context_candidates.append(
                (
                    score,
                    context_id,
                    start,
                    end,
                )
            )

        # If no context matches requested
        # consolidated/standalone dimension,
        # fall back to all contexts.
        if not context_candidates:

            for context_id, context in contexts.items():

                start, end = (
                    cls._context_period(
                        context
                    )
                )

                if end is None:
                    continue

                score = cls._context_score(
                    context,
                    period_end,
                )

                context_candidates.append(
                    (
                        score,
                        context_id,
                        start,
                        end,
                    )
                )

        context_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected_context_ids = {
            item[1]
            for item in context_candidates[:10]
        }

        # --------------------------------------------------------
        # Fact matching
        # --------------------------------------------------------

        def fact_matches(
            aliases: tuple[str, ...],
        ) -> Decimal | None:

            aliases_normalized = tuple(
                cls.normalize_key(
                    alias
                )
                for alias in aliases
            )

            candidates: list[
                tuple[int, Decimal]
            ] = []

            for (
                element,
                tag_name,
                value,
            ) in facts:

                context_ref = (
                    element.attrib.get(
                        "contextRef"
                    )
                )

                if (
                    context_ref
                    not in selected_context_ids
                ):
                    continue

                normalized_tag = (
                    cls.normalize_key(
                        tag_name
                    )
                )

                for index, alias in enumerate(
                    aliases_normalized
                ):

                    if normalized_tag == alias:

                        candidates.append(
                            (
                                1000 - index * 10,
                                value,
                            )
                        )

                    elif (
                        alias
                        in normalized_tag
                    ):

                        candidates.append(
                            (
                                500 - index * 10,
                                value,
                            )
                        )

            if not candidates:
                return None

            candidates.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            return candidates[0][1]

        # --------------------------------------------------------
        # Revenue
        # --------------------------------------------------------

        revenue = fact_matches(
            (
                "revenuefromoperations",
                "revenuefromoperation",
                "revenue",
                "revenuefromcontinuingoperations",
                "turnover",
                "netrevenue",
            )
        )

        # --------------------------------------------------------
        # Total income
        # --------------------------------------------------------

        total_income = fact_matches(
            (
                "totalincome",
                "totalrevenue",
                "income",
            )
        )

        # If revenue is absent, total income is
        # better than returning no number.
        if revenue is None:
            revenue = total_income

        # --------------------------------------------------------
        # Other income
        # --------------------------------------------------------

        other_income = fact_matches(
            (
                "otherincome",
                "otherincomeincludingshareofprofit",
            )
        )

        # --------------------------------------------------------
        # PAT
        # --------------------------------------------------------

        pat = fact_matches(
            (
                "profitforperiod",
                "profitfortheperiod",
                "profitaftertax",
                "netprofit",
                "profitloss",
                "profitlossfortheperiod",
                "profitattributabletoownersofparent",
            )
        )

        # Prefer profit attributable to owners
        # for consolidated companies.
        pat_owners = fact_matches(
            (
                "profitattributabletoownersofparent",
                "profitattributabletoowners",
                "profitlossattributabletoownersofparent",
            )
        )

        if (
            consolidated
            and pat_owners is not None
        ):
            pat = pat_owners

        # --------------------------------------------------------
        # EPS
        # --------------------------------------------------------

        diluted_eps = fact_matches(
            (
                "dilutedearningspershare",
                "dilutedeps",
                "dilutedepscontinuingoperations",
                "dilutedepsfromcontinuingoperations",
                "dilutedepsfromcontinuinganddiscontinuedoperations",
            )
        )

        basic_eps = fact_matches(
            (
                "basicearningspershare",
                "basiceps",
                "basicepscontinuingoperations",
                "basicepsfromcontinuingoperations",
                "basicepsfromcontinuinganddiscontinuedoperations",
            )
        )

        eps = (
            diluted_eps
            if diluted_eps is not None
            else basic_eps
        )

        # --------------------------------------------------------
        # EBITDA
        #
        # Most integrated filings don't provide a consistent
        # EBITDA tag.
        #
        # Compute:
        #
        # EBITDA = EBIT + Depreciation
        #
        # EBIT = PBT + Finance Cost
        #
        # EBITDA = PBT + Finance Cost + Depreciation
        # --------------------------------------------------------

        pbt = fact_matches(
            (
                "profitbeforetax",
                "profitbeforetaxation",
                "profitbeforetaxandexceptionalitems",
            )
        )

        finance_cost = fact_matches(
            (
                "financecosts",
                "financecost",
                "financecostexpense",
            )
        )

        depreciation = fact_matches(
            (
                "depreciation",
                "depreciationandamortisationexpense",
                "depreciationamortisation",
                "depreciationdepletionandamortisation",
            )
        )

        ebitda = None

        if (
            pbt is not None
            and finance_cost is not None
            and depreciation is not None
        ):

            ebitda = (
                pbt
                + finance_cost
                + depreciation
            )

        # Try direct EBITDA only if computation
        # wasn't possible.
        if ebitda is None:

            ebitda = fact_matches(
                (
                    "ebitda",
                    "earningsbeforeinteresttaxdepreciationandamortisation",
                )
            )

        # --------------------------------------------------------
        # Period
        # --------------------------------------------------------

        selected_period = None

        for item in context_candidates:

            score, context_id, start, end = item

            if period_end is None:
                selected_period = item
                break

            if end == period_end:
                selected_period = item
                break

        if selected_period is None:

            if context_candidates:
                selected_period = (
                    context_candidates[0]
                )

        if selected_period is not None:

            _score, _context_id, period_from, selected_end = (
                selected_period
            )

        else:

            period_from = None
            selected_end = period_end

        return {
            "period_from": period_from,
            "period_ended": selected_end,
            "revenue": revenue,
            "total_income": total_income,
            "other_income": other_income,
            "pat": pat,
            "pat_owners": pat_owners,
            "eps": eps,
            "basic_eps": basic_eps,
            "diluted_eps": diluted_eps,
            "pbt": pbt,
            "finance_cost": finance_cost,
            "depreciation": depreciation,
            "ebitda": ebitda,
        }

    # ============================================================
    # Parse integrated filing
    # ============================================================

    def parse_integrated_filing(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:

        symbol = (
            self._filing_symbol(row)
        )

        period_end = (
            self._filing_period_end(row)
        )

        company_name = (
            self._filing_company_name(row)
        )

        xbrl_url = (
            self._filing_xbrl_url(row)
        )

        consolidated = (
            self._filing_consolidated(row)
        )

        if not xbrl_url:

            return {
                "symbol": symbol,
                "company_name": company_name,
                "period_from": None,
                "period_ended": period_end,
                "consolidated": consolidated,
                "revenue": None,
                "pat": None,
                "eps": None,
                "basic_eps": None,
                "diluted_eps": None,
                "ebitda": None,
                "source_url": None,
                "broadcast_date": (
                    self._filing_broadcast_date(
                        row
                    )
                ),
                "raw": row,
            }

        xml_data = self._download(
            xbrl_url
        )

        parsed = self._parse_xbrl(
            xml_data,
            period_end=period_end,
            consolidated=consolidated,
        )

        return {
            "symbol": symbol,
            "company_name": company_name,
            "period_from": parsed.get(
                "period_from"
            ),
            "period_ended": parsed.get(
                "period_ended"
            ) or period_end,
            "consolidated": consolidated,

            "revenue": parsed.get(
                "revenue"
            ),

            "pat": parsed.get(
                "pat"
            ),

            "eps": parsed.get(
                "eps"
            ),

            "basic_eps": parsed.get(
                "basic_eps"
            ),

            "diluted_eps": parsed.get(
                "diluted_eps"
            ),

            "ebitda": parsed.get(
                "ebitda"
            ),

            "source_url": xbrl_url,

            "broadcast_date": (
                self._filing_broadcast_date(
                    row
                )
            ),

            "raw": row,
        }

    # ============================================================
    # Parse legacy NSE comparison row
    # ============================================================

    def parse_result_row(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:

        period_from = self.to_date(
            row.get("re_from_dt")
        )

        period_ended = self.to_date(
            row.get("re_to_dt")
        )

        # NSE legacy endpoint returns values in INR lakhs.
        revenue_lakh = self.to_decimal(
            row.get("re_total_inc")
        )

        revenue = None

        if revenue_lakh is not None:

            revenue = (
                revenue_lakh
                * Decimal("100000")
            )

        pat_lakh = self.to_decimal(
            row.get("re_net_profit")
        )

        pat = None

        if pat_lakh is not None:

            pat = (
                pat_lakh
                * Decimal("100000")
            )

        basic_eps = self.to_decimal(
            row.get(
                "re_basic_eps_for_cont_dic_opr"
            )
        )

        diluted_eps = self.to_decimal(
            row.get(
                "re_dilut_eps_for_cont_dic_opr"
            )
        )

        eps = (
            diluted_eps
            if diluted_eps is not None
            else basic_eps
        )

        return {
            "period_from": period_from,
            "period_ended": period_ended,

            "revenue": revenue,

            "pat": pat,

            "eps": eps,

            "basic_eps": basic_eps,

            "diluted_eps": diluted_eps,

            "ebitda": None,

            "raw": row,
        }

    # ============================================================
    # Convert integrated + legacy data into one list
    # ============================================================

    def get_results(
        self,
        symbol: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty"
            )

        results: list[
            dict[str, Any]
        ] = []

        # --------------------------------------------------------
        # 1. Current Integrated Filing data
        # --------------------------------------------------------

        try:

            filings = (
                self.get_integrated_filings(
                    symbol,
                    size=100,
                )
            )

            # Newest filings first.
            filings.sort(
                key=lambda row: (
                    self._filing_period_end(
                        row
                    )
                    or date.min
                ),
                reverse=True,
            )

            seen_periods: set[
                date
            ] = set()

            for filing in filings:

                try:

                    parsed = (
                        self.parse_integrated_filing(
                            filing
                        )
                    )

                except Exception:

                    # One malformed filing should not
                    # prevent the remaining quarters.
                    continue

                period_end = parsed.get(
                    "period_ended"
                )

                if period_end is None:
                    continue

                if period_end in seen_periods:
                    continue

                # Don't store completely empty filings.
                if (
                    parsed.get("revenue")
                    is None
                    and parsed.get("pat")
                    is None
                    and parsed.get("eps")
                    is None
                ):
                    continue

                seen_periods.add(
                    period_end
                )

                results.append(
                    parsed
                )

        except Exception:
            # Fall back to legacy data.
            pass

        # --------------------------------------------------------
        # 2. Legacy history
        # --------------------------------------------------------

        try:

            legacy_rows = (
                self.get_results_comparison(
                    symbol
                )
            )

            for row in legacy_rows:

                if not isinstance(
                    row,
                    dict,
                ):
                    continue

                parsed = (
                    self.parse_result_row(
                        row
                    )
                )

                period_end = parsed.get(
                    "period_ended"
                )

                if period_end is None:
                    continue

                # Don't duplicate a quarter already
                # supplied by Integrated Filing.
                if any(
                    existing.get(
                        "period_ended"
                    )
                    == period_end
                    for existing in results
                ):
                    continue

                if (
                    parsed.get("revenue")
                    is None
                    and parsed.get("pat")
                    is None
                    and parsed.get("eps")
                    is None
                ):
                    continue

                results.append(
                    parsed
                )

        except Exception:
            pass

        # --------------------------------------------------------
        # Sort newest first
        # --------------------------------------------------------

        results.sort(
            key=lambda item: (
                item.get(
                    "period_ended"
                )
                or date.min
            ),
            reverse=True,
        )

        return results[:limit]

    # ============================================================
    # Simple debug method
    # ============================================================

    def debug_integrated_filings(
        self,
        symbol: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        filings = (
            self.get_integrated_filings(
                symbol,
                size=100,
            )
        )

        output: list[
            dict[str, Any]
        ] = []

        for filing in filings[:limit]:

            output.append(
                {
                    "symbol": self._filing_symbol(
                        filing
                    ),
                    "company_name": (
                        self._filing_company_name(
                            filing
                        )
                    ),
                    "period_ended": (
                        self._filing_period_end(
                            filing
                        )
                    ),
                    "consolidated": (
                        self._filing_consolidated(
                            filing
                        )
                    ),
                    "xbrl_url": (
                        self._filing_xbrl_url(
                            filing
                        )
                    ),
                    "broadcast_date": (
                        self._filing_broadcast_date(
                            filing
                        )
                    ),
                    "raw": filing,
                }
            )

        return output
