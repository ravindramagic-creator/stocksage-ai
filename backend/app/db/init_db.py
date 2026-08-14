from sqlalchemy.orm import Session

from app.db.database import Base, SessionLocal, engine
from app.models.stock import Stock


INITIAL_STOCKS = [
    {
        "symbol": "HAL",
        "company_name": "Hindustan Aeronautics Limited",
        "exchange": "NSE",
        "sector": "Defence",
    },
    {
        "symbol": "BEL",
        "company_name": "Bharat Electronics Limited",
        "exchange": "NSE",
        "sector": "Defence",
    },
    {
        "symbol": "BHEL",
        "company_name": "Bharat Heavy Electricals Limited",
        "exchange": "NSE",
        "sector": "Capital Goods",
    },
    {
        "symbol": "KPITTECH",
        "company_name": "KPIT Technologies Limited",
        "exchange": "NSE",
        "sector": "Information Technology",
    },
    {
        "symbol": "TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "exchange": "NSE",
        "sector": "Automobile",
    },
    {
        "symbol": "BHARATFORG",
        "company_name": "Bharat Forge Limited",
        "exchange": "NSE",
        "sector": "Automobile",
    },
    {
        "symbol": "VBL",
        "company_name": "Varun Beverages Limited",
        "exchange": "NSE",
        "sector": "Food & Beverage",
    },
    {
        "symbol": "RVNL",
        "company_name": "Rail Vikas Nigam Limited",
        "exchange": "NSE",
        "sector": "Infrastructure",
    },
    {
        "symbol": "IDEAFORGE",
        "company_name": "ideaForge Technology Limited",
        "exchange": "NSE",
        "sector": "Defence",
    },
    {
        "symbol": "TATASTEEL",
        "company_name": "Tata Steel Limited",
        "exchange": "NSE",
        "sector": "Metals",
    },
]


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        for stock_data in INITIAL_STOCKS:
            existing_stock = (
                db.query(Stock)
                .filter(Stock.symbol == stock_data["symbol"])
                .first()
            )

            if existing_stock is None:
                db.add(Stock(**stock_data))

        db.commit()

    finally:
        db.close()
