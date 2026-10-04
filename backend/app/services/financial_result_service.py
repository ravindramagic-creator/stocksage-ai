from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.financial_result_repository import FinancialResultRepository


class FinancialResultService:

    RESULT_TOLERANCE_PCT = Decimal("1.0")

    def __init__(self, db: Session):
        self.repository = FinancialResultRepository(db)

    @staticmethod
    def calculate_growth(current: Decimal | None, previous: Decimal | None) -> Decimal | None:
        if current is None or previous is None or previous == 0:
            return None
        return ((current - previous) / abs(previous)) * Decimal("100")

    @staticmethod
    def calculate_surprise(actual: Decimal | None, estimate: Decimal | None) -> Decimal | None:
        if actual is None or estimate is None or estimate == 0:
            return None
        return ((actual - estimate) / abs(estimate)) * Decimal("100")

    @classmethod
    def classify_result(cls, actual: Decimal | None, estimate: Decimal | None) -> str:
        surprise = cls.calculate_surprise(actual, estimate)
        if surprise is None:
            return "UNKNOWN"
        if surprise > cls.RESULT_TOLERANCE_PCT:
            return "BEAT"
        if surprise < -cls.RESULT_TOLERANCE_PCT:
            return "MISS"
        return "MEET"

    @staticmethod
    def calculate_overall_result(
        revenue_result,
        eps_result,
        pat_result,
        ebitda_result,
    ) -> str:
        primary = [value for value in (revenue_result, eps_result) if value in {"BEAT", "MISS", "MEET"}]

        if len(primary) == 2:
            if primary.count("BEAT") == 2:
                return "BEAT"
            if primary.count("MISS") == 2:
                return "MISS"

        results = [
            value
            for value in (revenue_result, eps_result, pat_result, ebitda_result)
            if value in {"BEAT", "MISS", "MEET"}
        ]

        if not results:
            return "UNKNOWN"

        beats = results.count("BEAT")
        misses = results.count("MISS")
        if beats > misses:
            return "BEAT"
        if misses > beats:
            return "MISS"
        return "MEET"

    def get_latest(self, symbol: str):
        return self.repository.get_latest(symbol)

    def get_recent(self, symbol: str | None = None, limit: int = 20):
        return self.repository.get_recent(symbol=symbol, limit=limit)

    def get_by_period(self, symbol: str, period: date):
        return self.repository.get_by_period(symbol, period)
