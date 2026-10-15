from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import quote

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
    {"key": "healthcare", "name": "NIFTY Healthcare", "nse_index": "NIFTY HEALTHCARE", "symbol": "^CNXHEALTH"},
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
ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "3y", "5y"}
PERIOD_TO_YFINANCE = {"1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y", "3y": "3y", "5y": "5y"}


def _history_series(symbol: str, period: str) -> list[dict]:
    history = get_market_service().get_history(symbol, PERIOD_TO_YFINANCE[period], "1d")
    points = [point for point in history.points if point.close is not None]
    if not points:
        return []
    base = float(points[0].close)
    if base == 0:
        return []
    return [
        {
            "date": point.timestamp.date().isoformat(),
            "value": round(float(point.close) / base * 100, 4),
            "close": round(float(point.close), 2),
        }
        for point in points
    ]


def _get_constituents(index_name: str) -> list[dict]:
    cache_key = f"sector-constituents:{index_name}"
    cached = market_cache.get(cache_key)
    if cached is not None:
        return cached

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
    constituents.sort(key=lambda item: item["change_percent"] if item["change_percent"] is not None else -999, reverse=True)
    market_cache.set(cache_key, constituents, CACHE_TTL_SECONDS)
    return constituents


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
):
    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Unsupported period: {period}")
    sector = next((item for item in SECTORS if item["key"] == sector_key), None)
    if sector is None:
        raise HTTPException(status_code=404, detail=f"Unknown sector: {sector_key}")

    cache_key = f"sector-analysis:{sector_key}:{period}"
    cached = market_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        # Fetch index histories concurrently; both series are normalized to 100.
        with ThreadPoolExecutor(max_workers=2) as executor:
            sector_future = executor.submit(_history_series, sector["symbol"], period)
            benchmark_future = executor.submit(_history_series, BENCHMARK_SYMBOL, period)
            sector_history = sector_future.result()
            benchmark_history = benchmark_future.result()
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
    return payload
