"""Small helpers without Home Assistant imports (testable in isolation)."""

from __future__ import annotations

from .const import FAN_SPEED_MAX, FAN_SPEED_MIN

SPEED_RANGE = (FAN_SPEED_MIN, FAN_SPEED_MAX)


def speed_to_percentage(speed: int) -> int:
    """Map Enki fan speed (0–6) to a Home Assistant percentage (0–100)."""
    if speed <= 0:
        return 0
    low, high = SPEED_RANGE
    return int(round((speed - low) / (high - low) * 100))


def percentage_to_speed(percentage: int) -> int:
    """Map a Home Assistant percentage to an Enki fan speed."""
    if percentage <= 0:
        return 0
    low, high = SPEED_RANGE
    speed = int(round(low + (percentage / 100) * (high - low)))
    return max(FAN_SPEED_MIN, speed)
