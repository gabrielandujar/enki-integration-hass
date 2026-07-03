"""Battery health enum → percentage mapping (Lexman / Enki referentiel)."""

from __future__ import annotations

BATTERY_HEALTH_PERCENT: dict[str, float | None] = {
    "GOOD": 80,
    "LOW": 30,
    "LOW_INTERNAL_BATTERY_OF_DEVICE": 30,
    "REPLACE": 1,
    "UNKNOWN": None,
    "CRITICAL": 5,
}


def battery_health_to_percent(value: str | None) -> float | None:
    if value is None:
        return None
    return BATTERY_HEALTH_PERCENT.get(value.upper())
