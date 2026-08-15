EVENT_PRIORITY = {
    "RESULT": "HIGH",
    "ORDER": "HIGH",
    "ACQUISITION": "HIGH",
    "BONUS": "HIGH",
    "SPLIT": "HIGH",
    "DIVIDEND": "MEDIUM",
    "BOARD_MEETING": "MEDIUM",
    "PRESS_RELEASE": "MEDIUM",
    "NEWS": "LOW",
    "CORPORATE": "LOW",
    "PRICE_MOVE": "HIGH",
}


def get_priority(
    event_type: str,
) -> str:

    return EVENT_PRIORITY.get(
        event_type,
        "LOW",
    )
