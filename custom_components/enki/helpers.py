"""Small helpers without Home Assistant imports (testable in isolation)."""

from __future__ import annotations

from typing import Any

from .const import (
    AIRFLOW_ROTATION_CLOCKWISE,
    AIRFLOW_ROTATION_COUNTERCLOCKWISE,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    FAN_SPEED_MAX,
)

_ENKI_ROTATION_TO_DIRECTION: dict[str, str] = {
    AIRFLOW_ROTATION_CLOCKWISE: DIRECTION_FORWARD,
    AIRFLOW_ROTATION_COUNTERCLOCKWISE: DIRECTION_REVERSE,
    "COUNTER_CLOCKWISE": DIRECTION_REVERSE,
    "COUNTERCLOCKWISE": DIRECTION_REVERSE,
    "CCW": DIRECTION_REVERSE,
    "CW": DIRECTION_FORWARD,
    "FORWARD": DIRECTION_FORWARD,
    "REVERSE": DIRECTION_REVERSE,
    "SUMMER": DIRECTION_FORWARD,
    "WINTER": DIRECTION_REVERSE,
}

_DIRECTION_TO_ENKI_ROTATION: dict[str, str] = {
    DIRECTION_FORWARD: AIRFLOW_ROTATION_CLOCKWISE,
    DIRECTION_REVERSE: AIRFLOW_ROTATION_COUNTERCLOCKWISE,
}

# Home Assistant treats speed_count as the number of non-off speed steps.
# Percentage steps are 100 / speed_count (≈ 17 % per step for 6 speeds).


def speed_to_percentage(speed: int) -> int:
    """Map Enki fan speed (0–6) to a Home Assistant percentage (0–100)."""
    if speed <= 0:
        return 0
    return int(round(speed * 100 / FAN_SPEED_MAX))


def percentage_to_speed(percentage: int) -> int:
    """Map a Home Assistant percentage to an Enki fan speed (0–6)."""
    if percentage <= 0:
        return 0
    speed = int(round(percentage * FAN_SPEED_MAX / 100))
    return max(1, min(FAN_SPEED_MAX, speed))


def normalize_power_state(last_reported: Any, endpoint: int) -> str:
    """Parse check-electrical-power lastReportedValue (string or per-endpoint map)."""
    if isinstance(last_reported, str):
        return last_reported
    if isinstance(last_reported, dict):
        for key in (str(endpoint), endpoint):
            if key in last_reported:
                value = last_reported[key]
                if isinstance(value, str):
                    return value
        if len(last_reported) == 1:
            value = next(iter(last_reported.values()))
            if isinstance(value, str):
                return value
    return "OFF"


def enki_rotation_to_direction(value: Any) -> str | None:
    """Map Enki rotation / season value to a Home Assistant fan direction."""
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("rotation", "rotationDirection", "bladeDirection", "direction", "mode"):
            if key in value:
                value = value[key]
                break
        else:
            return None
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    return _ENKI_ROTATION_TO_DIRECTION.get(normalized)


def direction_to_enki_rotation(direction: str) -> str:
    """Map Home Assistant fan direction to an Enki rotation value."""
    mapped = _DIRECTION_TO_ENKI_ROTATION.get(direction)
    if mapped is None:
        raise ValueError(f"Unsupported fan direction: {direction}")
    return mapped
