from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import csv
from io import StringIO
from datetime import datetime, timezone
import requests
from fastapi import APIRouter, HTTPException, Query

from app.services.market_cache import market_cache
from app.services.market_service import get_market_service

router = APIRouter(prefix="/market/sectors", tags=["Sector Analysis"])

# Yahoo Finance symbols for NSE sector indices. NIFTY 50 is the common benchmark.
SECTORS = [
    {"key": "auto", "name": "NIFTY Auto", "nse_index": "NIFTY AUTO", "symbol": "^CNXAUTO"},
    {"key": "bank", "name": "NIFTY Bank", "nse_index": "NIFTY BANK", "symbol": "^NSEBANK"},
    {"key": "financial-services", "name": "NIFTY Financial Services", "nse_index": "NIFTY FINANCIAL SERVICES", "symbol": "^CNXFINANCE"},
    {"key": "fmcg", "name": "NIFTY FMCG", "nse_index": "NIFTY FMCG", "symbol": "^CNXFMCG"},
    {"key": "healthcare", "name": "NIFTY Healthcare", "nse_index": "NIFTY HEALTHCARE", "symbol": "^CNXHEALTH", "fallback_symbol": "HEALTHIETF.NS"},
    {"key": "consumer-durables", "name": "NIFTY Consumer Durables", "nse_index": "NIFTY CONSUMER DURABLES", "symbol": "^CNXCONSUM"},
    {"key": "it", "name": "NIFTY IT", "nse_index": "NIFTY IT", "symbol": "^CNXIT"},
    {"key": "media", "name": "NIFTY Media", "nse_index": "NIFTY MEDIA", "symbol": "^CNXMEDIA"},
    {"key": "metal", "name": "NIFTY Metal", "nse_index": "NIFTY METAL", "symbol": "^CNXMETAL"},
    {"key": "pharma", "name": "NIFTY Pharma", "nse_index": "NIFTY PHARMA", "symbol": "^CNXPHARMA"},
    {"key": "psu-bank", "name": "NIFTY PSU Bank", "nse_index": "NIFTY PSU BANK", "symbol": "^CNXPSUBANK"},
    {"key": "realty", "name": "NIFTY Realty", "nse_index": "NIFTY REALTY", "symbol": "^CNXREALTY"},
    {"key": "private-bank", "name": "NIFTY Private Bank", "nse_index": "NIFTY PRIVATE BANK", "symbol": "^NIFTYPVTBANK"},
    {"key": "oil-gas", "name": "NIFTY Oil & Gas", "nse_index": "NIFTY OIL & GAS", "symbol": "^CNXOILGAS"},
]
BENCHMARK_SYMBOL = "^NSEI"
CACHE_TTL_SECONDS = 300
ALLOWED_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "3y", "5y"}
PERIOD_CONFIG = {
    "1d": ("1d", "5m"),
    "5d": ("5d", "15m"),
    "1mo": ("1mo", "1d"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "3y": ("3y", "1d"),
    "5y": ("5y", "1d"),
}


def _history_series(symbol: str, period: str) -> list[dict]:
    history_period, interval = PERIOD_CONFIG[period]
    history = get_market_service().get_history(symbol, history_period, interval)
    points = [point for point in history.points if point.close is not None]
    if not points:
        return []
    base = float(points[0].close)
    if base == 0:
        return []
    intraday = period in {"1d", "5d"}
    return [
        {
            # Intraday timestamps must stay distinct; date-only keys collapse a whole session.
            "date": point.timestamp.isoformat() if intraday else point.timestamp.date().isoformat(),
            "value": round(float(point.close) / base * 100, 4),
            "close": round(float(point.close), 2),
        }
        for point in points
    ]


# Nifty Indices publishes constituent CSVs independently of the NSE quote API.
# These URLs are a fallback when NSE changes or blocks its equity-stockIndices endpoint.
CONSTITUENT_CSV_URLS = {
    "NIFTY AUTO": "https://www.niftyindices.com/IndexConstituent/ind_niftyauto_list.csv",
    "NIFTY BANK": "https://www.niftyindices.com/IndexConstituent/ind_niftybank_list.csv",
    "NIFTY FINANCIAL SERVICES": "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancialservices_list.csv",
    "NIFTY FMCG": "https://www.niftyindices.com/IndexConstituent/ind_niftyfmcg_list.csv",
    "NIFTY HEALTHCARE": "https://www.niftyindices.com/IndexConstituent/ind_niftyhealthcare_list.csv",
    "NIFTY CONSUMER DURABLES": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumerdurables_list.csv",
    "NIFTY IT": "https://www.niftyindices.com/IndexConstituent/ind_niftyit_list.csv",
    "NIFTY MEDIA": "https://www.niftyindices.com/IndexConstituent/ind_niftymedia_list.csv",
    "NIFTY METAL": "https://www.niftyindices.com/IndexConstituent/ind_niftymetal_list.csv",
    "NIFTY PHARMA": "https://www.niftyindices.com/IndexConstituent/ind_niftypharma_list.csv",
    "NIFTY PSU BANK": "https://www.niftyindices.com/IndexConstituent/ind_niftypsubank_list.csv",
    "NIFTY REALTY": "https://www.niftyindices.com/IndexConstituent/ind_niftyrealty_list.csv",
    "NIFTY PRIVATE BANK": "https://www.niftyindices.com/IndexConstituent/ind_niftyprivatebank_list.csv",
    "NIFTY OIL & GAS": "https://www.niftyindices.com/IndexConstituent/ind_niftyoilgas_list.csv",
}


def _constituents_from_csv(index_name: str) -> list[dict]:
    url = CONSTITUENT_CSV_URLS.get(index_name.upper())
    if not url:
        return []
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
            "Accept": "text/csv,*/*",
            "Referer": "https://www.niftyindices.com/",
        },
        timeout=20,
    )
    response.raise_for_status()
    rows = csv.DictReader(StringIO(response.content.decode("utf-8-sig", errors="replace")))
    constituents = []
    for row in rows:
        normalized = {str(key or "").strip().lower(): str(value or "").strip() for key, value in row.items()}
        symbol = (normalized.get("symbol") or normalized.get("ticker") or "").upper()
        if not symbol:
            continue
        company_name = (
            normalized.get("company name")
            or normalized.get("companyname")
            or normalized.get("name")
            or symbol
        )
        constituents.append({
            "symbol": symbol,
            "company_name": company_name,
            "price": None,
            "change_percent": None,
            "volume": None,
        })
    return constituents


# Last-resort constituent universe so the UI and comparison chart still work
# if both public index constituents endpoints are unavailable. This is a fallback
# universe, not a claim that every entry is in the latest official index rebalance.
STATIC_CONSTITUENTS = {
    "NIFTY AUTO": ["MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "TVSMOTOR", "BOSCHLTD", "ASHOKLEY", "SONACOMS", "TIINDIA", "BHARATFORG"],
    "NIFTY BANK": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "BANKBARODA", "PNB", "IDFCFIRSTB", "FEDERALBNK", "AUBANK", "BANDHANBNK"],
    "NIFTY FINANCIAL SERVICES": ["HDFCBANK", "ICICIBANK", "SBIN", "BAJFINANCE", "BAJAJFINSV", "KOTAKBANK", "AXISBANK", "SHRIRAMFIN", "CHOLAFIN", "JIOFIN", "HDFCLIFE", "SBILIFE"],
    "NIFTY FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", "GODREJCP", "DABUR", "MARICO", "COLPAL", "VBL", "UNITDSPR", "EMAMILTD"],
    "NIFTY HEALTHCARE": ["SUNPHARMA", "DIVISLAB", "CIPLA", "DRREDDY", "APOLLOHOSP", "MAXHEALTH", "FORTIS", "MANKIND", "ZYDUSLIFE", "TORNTPHARM", "LUPIN", "AUROPHARMA"],
    "NIFTY CONSUMER DURABLES": ["TITAN", "HAVELLS", "DIXON", "VOLTAS", "BLUESTARCO", "CROMPTON", "KALYANKJIL", "AMBER", "WHIRLPOOL", "RAJESHEXPO"],
    "NIFTY IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "KPITTECH", "OFSS", "LTTS"],
    "NIFTY MEDIA": ["SUNTV", "ZEEL", "PVRINOX", "NAZARA", "NETWORK18", "DISHTV", "SAREGAMA", "TIPSMUSIC", "DBCORP", "JAGRAN"],
    "NIFTY METAL": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "COALINDIA", "JINDALSTEL", "NMDC", "SAIL", "NATIONALUM", "APLAPOLLO", "HINDZINC"],
    "NIFTY PHARMA": ["SUNPHARMA", "DRREDDY", "DIVISLAB", "CIPLA", "TORNTPHARM", "LUPIN", "ZYDUSLIFE", "MANKIND", "AUROPHARMA", "ALKEM", "GLENMARK", "IPCA", "LAURUSLABS", "BIOCON", "ABBOTINDIA", "GLAND", "NATCOPHARM", "GRANULES", "JBCHEPHARM"],
    "NIFTY PSU BANK": ["SBIN", "BANKBARODA", "PNB", "CANBK", "UNIONBANK", "INDIANB", "BANKINDIA", "MAHABANK", "IOB", "CENTRALBK", "UCOBANK", "PSB"],
    "NIFTY REALTY": ["DLF", "GODREJPROP", "PRESTIGE", "OBEROIRLTY", "LODHA", "PHOENIXLTD", "BRIGADE", "SOBHA", "ANANTRAJ", "MAHLIFE"],
    "NIFTY PRIVATE BANK": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "IDFCFIRSTB", "FEDERALBNK", "AUBANK", "BANDHANBNK", "YESBANK", "RBLBANK", "KARURVYSYA"],
    "NIFTY OIL & GAS": ["RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "HINDPETRO", "IGL", "PETRONET", "ATGL", "OIL", "GUJGASLTD", "MGL"],
}


def _static_constituents(index_name: str) -> list[dict]:
    return [
        {
            "symbol": symbol,
            "company_name": symbol,
            "price": None,
            "change_percent": None,
            "volume": None,
        }
        for symbol in STATIC_CONSTITUENTS.get(index_name.upper(), [])
    ]


def _get_constituents(index_name: str) -> list[dict]:
    cache_key = f"sector-constituents:{index_name}"
    cached = market_cache.get(cache_key)
    # Do not reuse an empty result from an earlier upstream outage.
    if cached:
        return cached

    nse_error = None
    try:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        })
        session.get("https://www.nseindia.com/", timeout=10)
        response = session.get(
            "https://www.nseindia.com/api/equity-stockIndices",
            params={"index": index_name},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data") or []
        constituents = []
        for row in rows:
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol or symbol == index_name.upper():
                continue
            try:
                price = float(row.get("lastPrice")) if row.get("lastPrice") is not None else None
            except (TypeError, ValueError):
                price = None
            try:
                change_percent = float(row.get("pChange")) if row.get("pChange") is not None else None
            except (TypeError, ValueError):
                change_percent = None
            constituents.append({
                "symbol": symbol,
                "company_name": row.get("meta", {}).get("companyName") or row.get("companyName") or symbol,
                "price": price,
                "change_percent": change_percent,
                "volume": row.get("totalTradedVolume"),
            })
        if constituents:
            constituents.sort(
                key=lambda item: item["change_percent"] if item["change_percent"] is not None else -999,
                reverse=True,
            )
            market_cache.set(cache_key, constituents, CACHE_TTL_SECONDS)
            return constituents
    except Exception as exc:
        nse_error = exc

    csv_error = None
    try:
        constituents = _constituents_from_csv(index_name)
        if constituents:
            market_cache.set(cache_key, constituents, CACHE_TTL_SECONDS)
            return constituents
    except Exception as exc:
        csv_error = exc

    # Keep constituent selection usable even during upstream outages. Price and
    # daily-change fields remain null until live quote data can be fetched.
    constituents = _static_constituents(index_name)
    if constituents:
        market_cache.set(cache_key, constituents, CACHE_TTL_SECONDS)
        return constituents

    raise RuntimeError(
        f"No constituents available for {index_name}; "
        f"NSE error={nse_error or 'no data'}, CSV error={csv_error or 'no data'}"
    )


@router.get("")
def list_sector_indices():
    return [
        {"key": item["key"], "name": item["name"], "symbol": item["symbol"]}
        for item in SECTORS
    ]


@router.get("/{sector_key}")
def get_sector_analysis(
    sector_key: str,
    period: str = Query("6mo"),
    symbols: str | None = Query(None, description="Optional comma-separated constituent symbols to compare; maximum 8"),
):
    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Unsupported period: {period}")
    sector = next((item for item in SECTORS if item["key"] == sector_key), None)
    if sector is None:
        raise HTTPException(status_code=404, detail=f"Unknown sector: {sector_key}")

    selected_symbols = list(dict.fromkeys(
        item.strip().upper() for item in (symbols or "").split(",") if item.strip()
    ))
    if len(selected_symbols) > 8:
        raise HTTPException(status_code=400, detail="A maximum of 8 constituents can be compared at once")

    cache_key = f"sector-analysis:{sector_key}:{period}"
    cached = market_cache.get(cache_key)

    # A few NSE indices do not have a working Yahoo Finance symbol.
    # In those cases use a clearly labelled ETF proxy rather than returning 502.
    sector_history_source = "official_index"
    sector_history_is_proxy = False
    try:
        if (
            cached is not None
            and cached.get("sector_history")
            and cached.get("nifty50_history")
            and not cached.get("sector_history_is_proxy", False)
        ):
            sector_history = cached["sector_history"]
            benchmark_history = cached["nifty50_history"]
        else:
            with ThreadPoolExecutor(max_workers=2) as executor:
                sector_future = executor.submit(_history_series, sector["symbol"], period)
                benchmark_future = executor.submit(_history_series, BENCHMARK_SYMBOL, period)
                sector_result = None
                sector_error = None
                try:
                    sector_result = sector_future.result()
                except Exception as exc:
                    sector_error = exc
                benchmark_history = benchmark_future.result()

            if sector_result:
                sector_history = sector_result
            else:
                fallback_symbol = sector.get("fallback_symbol")
                if not fallback_symbol:
                    raise RuntimeError(
                        f"No historical data returned for {sector['name']}: {sector_error or 'empty history'}"
                    )
                sector_history = _history_series(fallback_symbol, period)
                if not sector_history:
                    raise RuntimeError(
                        f"Both {sector['symbol']} and fallback {fallback_symbol} returned no history"
                    )
                sector_history_source = fallback_symbol
                sector_history_is_proxy = True

        if not sector_history:
            raise RuntimeError(f"No historical data returned for {sector['name']}")
        if not benchmark_history:
            raise RuntimeError("No NIFTY 50 historical data returned")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to load sector history: {exc}") from exc

    try:
        constituents = _get_constituents(sector["nse_index"])
    except Exception as exc:
        # Index chart remains useful even when NSE's constituents endpoint is unavailable.
        constituents = []
        constituents_error = f"NSE constituents are temporarily unavailable: {exc}"
    else:
        constituents_error = None

    def total_return(series: list[dict]) -> float | None:
        if len(series) < 2:
            return None
        return round((series[-1]["value"] / series[0]["value"] - 1) * 100, 2)

    sector_return = total_return(sector_history)
    benchmark_return = total_return(benchmark_history)
    payload = {
        "key": sector["key"],
        "name": sector["name"],
        "period": period,
        "sector_history_source": sector_history_source,
        "sector_history_is_proxy": sector_history_is_proxy,
        "chart_label": f"{sector['name']} (ETF proxy)" if sector_history_is_proxy else sector["name"],
        "sector_return_percent": sector_return,
        "nifty50_return_percent": benchmark_return,
        "excess_return_percent": round(sector_return - benchmark_return, 2) if sector_return is not None and benchmark_return is not None else None,
        "sector_history": sector_history,
        "nifty50_history": benchmark_history,
        "constituents": constituents,
        "constituents_error": constituents_error,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    market_cache.set(cache_key, payload, CACHE_TTL_SECONDS)

    if selected_symbols:
        allowed_symbols = {item["symbol"] for item in constituents}
        invalid_symbols = [symbol for symbol in selected_symbols if symbol not in allowed_symbols]
        if invalid_symbols:
            raise HTTPException(
                status_code=400,
                detail=f"Selected symbols are not constituents of {sector['name']}: {', '.join(invalid_symbols)}",
            )
        with ThreadPoolExecutor(max_workers=min(8, len(selected_symbols))) as executor:
            futures = {
                symbol: executor.submit(_history_series, f"{symbol}.NS", period)
                for symbol in selected_symbols
            }
            constituent_histories = {}
            for symbol, future in futures.items():
                try:
                    constituent_histories[symbol] = future.result()
                except Exception:
                    # One delisted, renamed, or temporarily unavailable ticker
                    # should not break the entire multi-stock comparison request.
                    constituent_histories[symbol] = []
        payload = {**payload, "constituent_histories": constituent_histories}
    else:
        payload = {**payload, "constituent_histories": {}}
    return payload
