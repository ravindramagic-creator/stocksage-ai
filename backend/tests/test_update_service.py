from datetime import datetime, timezone
from unittest.mock import Mock

from app.services.update_service import (
    UpdateService,
)


def test_duplicate_event_is_not_created():

    repository = Mock()

    repository.exists.return_value = True

    service = UpdateService.__new__(
        UpdateService
    )

    service.repository = repository

    result = service.create_event(
        symbol="HAL",
        event_type="PRICE_MOVE",
        title="HAL is up 4%",
        description="HAL moved 4%",
        source="Market Data",
        event_key="PRICE:HAL:2026-08-15:up",
        event_time=datetime.now(
            timezone.utc
        ),
    )

    assert result is None

    repository.create.assert_not_called()
