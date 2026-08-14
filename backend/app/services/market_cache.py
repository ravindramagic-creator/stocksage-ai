import time
from dataclasses import dataclass
from threading import Lock
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: float


class MarketCache:

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            if time.monotonic() >= entry.expires_at:
                del self._cache[key]
                return None

            return entry.value

    def set(
        self,
        key: str,
        value,
        ttl_seconds: int,
    ) -> None:

        with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=(
                    time.monotonic()
                    + ttl_seconds
                ),
            )

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


market_cache = MarketCache()
