from abc import ABC, abstractmethod
from datetime import date


class AutoSalesProvider(ABC):
    """Source adapter for normalized monthly automobile data."""

    @abstractmethod
    def fetch_month(self, month: date) -> list[dict]:
        raise NotImplementedError
