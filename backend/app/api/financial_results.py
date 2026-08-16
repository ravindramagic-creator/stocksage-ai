from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.financial_result import (
    FinancialResultResponse,
)
from app.services.financial_result_service import (
    FinancialResultService,
)


router = APIRouter(
    prefix="/financial-results",
    tags=["Financial Results"],
)


@router.get(
    "",
    response_model=list[
        FinancialResultResponse
    ],
)
def get_financial_results(
    symbol: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):

    service = FinancialResultService(db)

    return service.get_recent(
        symbol=symbol,
        limit=limit,
    )


@router.get(
    "/{symbol}/latest",
    response_model=FinancialResultResponse,
)
def get_latest_result(
    symbol: str,
    db: Session = Depends(get_db),
):

    service = FinancialResultService(db)

    result = service.get_latest(
        symbol
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No financial results "
                f"found for {symbol}"
            ),
        )

    return result
