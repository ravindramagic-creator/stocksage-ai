from fastapi import APIRouter, Query

from app.schemas.market_news import MarketNewsItemResponse
from app.services.market_news_service import MarketNewsService


router = APIRouter(
    prefix="/market-news",
    tags=["Market News"],
)


@router.get(
    "",
    response_model=list[MarketNewsItemResponse],
)
def get_market_news(
    limit: int = Query(
        12,
        ge=1,
        le=30,
    ),
):
    return MarketNewsService.get_latest(
        limit=limit,
    )
