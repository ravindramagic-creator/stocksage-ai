from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketEvent:
    symbol: str
    event_type: str
    title: str
    description: str | None = None

    source: str | None = None
    source_url: str | None = None

    old_value: float | None = None
    new_value: float | None = None

    event_key: str = ""

    event_time: datetime | None = None


class EventProvider(ABC):

    @abstractmethod
    def get_events(
        self,
        symbol: str,
    ) -> list[MarketEvent]:
        raise NotImplementedError
