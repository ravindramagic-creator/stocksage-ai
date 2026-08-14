from fastapi import APIRouter, HTTPException

from app.services.stock_discovery import (
    StockDiscoveryService,
)


router = APIRouter(
    prefix="/stock-search",
    tags=["Stock Discovery"],
)


@router.get("")
def search_stock_market(
    q: str,
):
    query = q.strip()

    if len(query) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Search query must contain "
                "at least 2 characters"
            ),
        )

    try:
        service = StockDiscoveryService()

        results = service.search(query)

        return {
            "query": query,
            "results": results,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to search the stock "
                "market currently"
            ),
        ) from exc
