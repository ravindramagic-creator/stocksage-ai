from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.financial_result import FinancialResultResponse
from app.services.financial_result_ingestion import FinancialResultIngestion
from app.services.financial_result_service import FinancialResultService
from app.services.nse_financial_result_provider import NSEFinancialResultProvider


router = APIRouter(
    prefix="/financial-results",
    tags=["Financial Results"],
)

MAX_FINANCIAL_RESULT_LIMIT = 40


def _needs_refresh(results) -> bool:
    if not results:
        return True

    for result in results:
        actuals_missing = (
            result.revenue is None
            and result.pat is None
            and result.eps is None
        )
        eps_missing = result.eps is None
        estimates_missing = (
            result.revenue_estimate is None
            and result.ebitda_estimate is None
            and result.pat_estimate is None
            and result.eps_estimate is None
        )

        if actuals_missing or eps_missing or estimates_missing:
            return True

    return False


def _calculate_growth(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return ((current - previous) / abs(previous)) * Decimal("100")


def _repair_actuals_from_legacy(symbol: str, db: Session) -> None:
    """Repair rows where integrated XBRL has metadata but missing actual facts."""
    symbol = symbol.upper().strip()
    if not symbol:
        return

    provider = NSEFinancialResultProvider()
    service = FinancialResultService(db)

    try:
        rows = provider.get_results_comparison(symbol)
    except Exception:
        return

    parsed = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            item = provider.parse_result_row(row)
        except Exception:
            continue
        period = item.get("period_ended")
        if period is not None:
            parsed.append(item)

    parsed.sort(key=lambda item: item["period_ended"], reverse=True)
    values_by_period = {item["period_ended"]: item for item in parsed}

    for period, item in values_by_period.items():
        result = service.get_by_period(symbol, period)
        if result is None:
            continue

        if result.revenue is None and item.get("revenue") is not None:
            result.revenue = item["revenue"]
        if result.pat is None and item.get("pat") is not None:
            result.pat = item["pat"]
        if result.eps is None and item.get("eps") is not None:
            result.eps = item["eps"]

        previous_quarter = None
        previous_year = None
        for candidate_period, candidate in values_by_period.items():
            days = (period - candidate_period).days
            if 70 <= days <= 110 and previous_quarter is None:
                previous_quarter = candidate
            if 330 <= days <= 400 and previous_year is None:
                previous_year = candidate

        if result.revenue_yoy is None:
            result.revenue_yoy = _calculate_growth(
                result.revenue,
                previous_year.get("revenue") if previous_year else None,
            )
        if result.revenue_qoq is None:
            result.revenue_qoq = _calculate_growth(
                result.revenue,
                previous_quarter.get("revenue") if previous_quarter else None,
            )
        if result.pat_yoy is None:
            result.pat_yoy = _calculate_growth(
                result.pat,
                previous_year.get("pat") if previous_year else None,
            )
        if result.pat_qoq is None:
            result.pat_qoq = _calculate_growth(
                result.pat,
                previous_quarter.get("pat") if previous_quarter else None,
            )
        if result.eps_yoy is None:
            result.eps_yoy = _calculate_growth(
                result.eps,
                previous_year.get("eps") if previous_year else None,
            )

        # A BEAT/MISS badge is meaningful only when a consensus estimate exists.
        has_estimate = any(
            value is not None
            for value in (
                result.revenue_estimate,
                result.ebitda_estimate,
                result.pat_estimate,
                result.eps_estimate,
            )
        )
        if not has_estimate:
            result.revenue_result = None
            result.ebitda_result = None
            result.pat_result = None
            result.eps_result = None
            result.revenue_surprise_pct = None
            result.ebitda_surprise_pct = None
            result.pat_surprise_pct = None
            result.eps_surprise_pct = None
            result.overall_result = "UNKNOWN"

        summary_parts = []
        if result.revenue_yoy is not None:
            summary_parts.append(f"Revenue {result.revenue_yoy:+.1f}% YoY")
        if result.pat_yoy is not None:
            summary_parts.append(f"PAT {result.pat_yoy:+.1f}% YoY")
        if result.eps_yoy is not None:
            summary_parts.append(f"EPS {result.eps_yoy:+.1f}% YoY")
        if summary_parts:
            result.summary = ", ".join(summary_parts) + "."

    db.commit()


def _sync(symbol: str, limit: int, db: Session):
    ingestion = FinancialResultIngestion(db)

    try:
        ingestion.ingest(symbol, limit)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to fetch financial results: {exc}",
        ) from exc

    _repair_actuals_from_legacy(symbol, db)


@router.get("", response_model=list[FinancialResultResponse])
def get_financial_results(
    symbol: str | None = None,
    limit: int = 40,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, MAX_FINANCIAL_RESULT_LIMIT))

    service = FinancialResultService(db)
    results = service.get_recent(symbol=symbol, limit=limit)

    if symbol and _needs_refresh(results):
        _sync(symbol, limit, db)
        results = service.get_recent(symbol=symbol, limit=limit)

    return results


@router.post("/{symbol}/sync", response_model=list[FinancialResultResponse])
def sync_financial_results(
    symbol: str,
    limit: int = 40,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, MAX_FINANCIAL_RESULT_LIMIT))
    _sync(symbol, limit, db)

    service = FinancialResultService(db)
    return service.get_recent(symbol=symbol, limit=limit)


@router.get("/{symbol}/latest", response_model=FinancialResultResponse)
def get_latest_result(symbol: str, db: Session = Depends(get_db)):
    service = FinancialResultService(db)
    result = service.get_latest(symbol)

    needs_sync = (
        result is None
        or result.revenue is None
        or result.pat is None
        or result.eps is None
        or (
            result.revenue_estimate is None
            and result.ebitda_estimate is None
            and result.pat_estimate is None
            and result.eps_estimate is None
        )
    )

    if needs_sync:
        _sync(symbol, MAX_FINANCIAL_RESULT_LIMIT, db)
        result = service.get_latest(symbol)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No financial results found for {symbol}",
        )

    return result
