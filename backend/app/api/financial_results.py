from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.financial_result import (
    FinancialResultResponse,
)

from app.services.financial_result_service import (
    FinancialResultService,
)

from app.services.financial_result_ingestion import (
    FinancialResultIngestion,
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

    results = service.get_recent(
        symbol=symbol,
        limit=limit,
    )

    # Automatically fetch from Yahoo when
    # this stock has no financial results
    # stored in our database.
    if (
        symbol
        and not results
    ):
        ingestion = (
            FinancialResultIngestion(db)
        )

        try:
            ingestion.ingest(
                symbol,
                min(limit, 20),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to fetch financial "
                    "results from Yahoo Finance"
                ),
            ) from exc

        results = service.get_recent(
            symbol=symbol,
            limit=limit,
        )

    return results


@router.post(
    "/{symbol}/sync",
    response_model=list[
        FinancialResultResponse
    ],
)
def sync_financial_results(
    symbol: str,
    limit: int = 8,
    db: Session = Depends(get_db),
):
    ingestion = (
        FinancialResultIngestion(db)
    )

    try:
        ingestion.ingest(
            symbol,
            min(limit, 20),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to fetch financial "
                "results from Yahoo Finance"
            ),
        ) from exc

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

    # Lazy-fetch if database is empty.
    if result is None:
        ingestion = (
            FinancialResultIngestion(db)
        )

        try:
            ingestion.ingest(
                symbol,
                8,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to fetch financial "
                    "results from Yahoo Finance"
                ),
            ) from exc

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
