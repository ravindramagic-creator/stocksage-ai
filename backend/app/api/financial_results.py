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


# ============================================================
# GET recent financial results
# ============================================================

@router.get(
    "",
    response_model=list[
        FinancialResultResponse
    ],
)
def get_financial_results(
    symbol: str | None = None,
    limit: int = 8,
    db: Session = Depends(get_db),
):

    limit = max(
        1,
        min(limit, 20),
    )

    service = FinancialResultService(
        db
    )

    results = service.get_recent(
        symbol=symbol,
        limit=limit,
    )

    # --------------------------------------------------------
    # Automatically repair missing data.
    # --------------------------------------------------------

    needs_sync = False

    if symbol and not results:

        needs_sync = True

    elif symbol and results:

        for result in results:

            if (
                result.revenue is None
                and result.pat is None
                and result.eps is None
            ):

                needs_sync = True

                break

    # --------------------------------------------------------
    # NSE sync
    # --------------------------------------------------------

    if symbol and needs_sync:

        ingestion = (
            FinancialResultIngestion(db)
        )

        try:

            ingestion.ingest(
                symbol,
                limit,
            )

        except Exception as exc:

            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to fetch "
                    "financial results "
                    "from NSE"
                ),
            ) from exc

        results = service.get_recent(
            symbol=symbol,
            limit=limit,
        )

    return results


# ============================================================
# POST manual sync
# ============================================================

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

    limit = max(
        1,
        min(limit, 20),
    )

    ingestion = (
        FinancialResultIngestion(db)
    )

    try:

        results = ingestion.ingest(
            symbol,
            limit,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to fetch "
                "financial results "
                "from NSE: "
                f"{exc}"
            ),
        ) from exc

    return results


# ============================================================
# GET latest
# ============================================================

@router.get(
    "/{symbol}/latest",
    response_model=FinancialResultResponse,
)
def get_latest_result(
    symbol: str,
    db: Session = Depends(get_db),
):

    service = FinancialResultService(
        db
    )

    result = service.get_latest(
        symbol
    )

    # --------------------------------------------------------
    # If missing or empty, sync NSE.
    # --------------------------------------------------------

    needs_sync = (
        result is None
        or (
            result.revenue is None
            and result.pat is None
            and result.eps is None
        )
    )

    if needs_sync:

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
                    "Unable to fetch "
                    "financial results "
                    "from NSE"
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
