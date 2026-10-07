from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.database import Base, SessionLocal, engine
from app.models.stock import Stock
from app.models.subscription import Subscription
from app.models.update_event import UpdateEvent
from app.models.auto_sales import AutoSales  # noqa: F401
from app.models.screener_snapshot import ScreenerSnapshot  # noqa: F401
from app.models.market_snapshot import MarketSnapshot  # noqa: F401

INITIAL_STOCKS = [
    {"symbol": "HAL", "company_name": "Hindustan Aeronautics Limited", "exchange": "NSE", "sector": "Defence"},
    {"symbol": "BEL", "company_name": "Bharat Electronics Limited", "exchange": "NSE", "sector": "Defence"},
    {"symbol": "BHEL", "company_name": "Bharat Heavy Electricals Limited", "exchange": "NSE", "sector": "Capital Goods"},
    {"symbol": "KPITTECH", "company_name": "KPIT Technologies Limited", "exchange": "NSE", "sector": "Information Technology"},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Limited", "exchange": "NSE", "sector": "Automobile"},
    {"symbol": "BHARATFORG", "company_name": "Bharat Forge Limited", "exchange": "NSE", "sector": "Automobile"},
    {"symbol": "VBL", "company_name": "Varun Beverages Limited", "exchange": "NSE", "sector": "Food & Beverage"},
    {"symbol": "RVNL", "company_name": "Rail Vikas Nigam Limited", "exchange": "NSE", "sector": "Infrastructure"},
    {"symbol": "IDEAFORGE", "company_name": "ideaForge Technology Limited", "exchange": "NSE", "sector": "Defence"},
    {"symbol": "TATASTEEL", "company_name": "Tata Steel Limited", "exchange": "NSE", "sector": "Metals"},
]


def _ensure_columns(table: str, columns: dict[str, str]) -> None:
    inspector = inspect(engine)
    existing = {column["name"] for column in inspector.get_columns(table)}

    missing = [
        (name, definition)
        for name, definition in columns.items()
        if name not in existing
    ]

    if not missing:
        return

    with engine.begin() as connection:
        for name, definition in missing:
            connection.execute(
                text(
                    f'ALTER TABLE "{table}" '
                    f'ADD COLUMN "{name}" {definition}'
                )
            )


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)

    # create_all() does not add new columns to an existing SQLite database.
    # Keep the lightweight application startup migration in sync with the
    # technical-indicator models so existing deployments are upgraded safely.
    _ensure_columns(
        "market_snapshots",
        {
            "rsi_weekly": "FLOAT",
            "rsi_monthly": "FLOAT",
            "momentum_3m": "FLOAT",
        },
    )
    _ensure_columns(
        "screener_snapshots",
        {
            "rsi_weekly": "FLOAT",
            "rsi_monthly": "FLOAT",
            "momentum_3m": "FLOAT",
        },
    )

    db: Session = SessionLocal()
    try:
        for stock_data in INITIAL_STOCKS:
            existing_stock = db.query(Stock).filter(Stock.symbol == stock_data["symbol"]).first()
            if existing_stock is None:
                db.add(Stock(**stock_data))
        db.commit()
    finally:
        db.close()
