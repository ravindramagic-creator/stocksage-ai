from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.providers.vahan_retail_provider import VahanRetailProvider
from app.schemas.auto_sales import AutoSalesResponse
from app.services.auto_sales_ingestion import AutoSalesIngestion
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


@router.post("/sync")
def sync_auto_sales(
    month: date | None = Query(
        None,
        description="First day of month; omit to sync all available history",
    ),
    segment: str | None = Query(
        None,
        description="PV, 2W, 3W, CV or TRACTOR",
    ),
    db: Session = Depends(get_db),
):
    provider = VahanRetailProvider()
    ingestion = AutoSalesIngestion(db, provider)

    if month:
        count = ingestion.ingest_month(month.replace(day=1))
    else:
        records = provider.fetch_history(segment)
        for record in records:
            ingestion.repository.upsert(record)
        ingestion.repository.db.commit()
        count = len(records)

    return {
        "records": count,
        "source": "VAHAN_DERIVED",
        "segment": segment.upper() if segment else "ALL",
        "month": month.replace(day=1).isoformat() if month else None,
    }
