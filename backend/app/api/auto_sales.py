from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auto_sales import AutoSalesResponse
from app.services.auto_sales_service import AutoSalesService

router = APIRouter(prefix="/auto-sales", tags=["Auto Sales"])


@router.get("", response_model=list[AutoSalesResponse])
def get_auto_sales(
    symbol: str | None = Query(None),
    segment: str | None = Query(None),
    start_month: date | None = Query(None),
    end_month: date | None = Query(None),
    data_type: str | None = Query(None, description="REGISTRATION or SALES"),
    db: Session = Depends(get_db),
):
    return AutoSalesService(db).get_sales(
        symbol=symbol,
        segment=segment,
        start_month=start_month,
        end_month=end_month,
        data_type=data_type,
    )
