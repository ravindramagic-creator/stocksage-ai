from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.financial_result import FinancialResultResponse
from app.services.financial_result_ingestion import FinancialResultIngestion
from app.services.financial_result_service import FinancialResultService


router = APIRouter(
    prefix="/financial-results",
    tags=["Financial Results"],
)

MAX_FINANCIAL_RESULT_LIMIT = 40


def _needs_refresh(results) -> bool:
    """Return True when stored financial data is incomplete.

    Older rows can contain revenue/PAT but still have missing EPS or
    analyst-consensus fields. Those rows previously bypassed ingestion,
    leaving the UI with misleading dashes forever.
    """
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


def _sync(
    symbol: str,
    limit: int,
    db: Session,
):
    ingestion = FinancialResultIngestion(db)

    try:
        ingestion.ingest(symbol, limit)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to fetch financial results: {exc}",
        ) from exc


@router.get(
    "",
    response_model=list[FinancialResultResponse],
)
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


@router.post(
    "/{symbol}/sync",
    response_model=list[FinancialResultResponse],
)
def sync_financial_results(
    symbol: str,
    limit: int = 40,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, MAX_FINANCIAL_RESULT_LIMIT))

    _sync(symbol, limit, db)

    service = FinancialResultService(db)
    return service.get_recent(symbol=symbol, limit=limit)


@router.get(
    "/{symbol}/latest",
    response_model=FinancialResultResponse,
)
def get_latest_result(
    symbol: str,
    db: Session = Depends(get_db),
):
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
