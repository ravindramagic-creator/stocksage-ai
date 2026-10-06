from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.fundamental_analysis import FundamentalAnalysisResponse
from app.services.fundamental_analysis_service import FundamentalAnalysisService


router = APIRouter(
    prefix="/fundamental-analysis",
    tags=["Fundamental Analysis"],
)


@router.get(
    "/{symbol}",
    response_model=FundamentalAnalysisResponse,
)
def get_fundamental_analysis(
    symbol: str,
    db: Session = Depends(get_db),
):
    result = FundamentalAnalysisService(db).analyze(symbol)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fundamental data not available for {symbol.upper()}",
        )

    return result
