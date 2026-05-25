"""Small helpers without Home Assistant imports (testable in isolation)."""

from __future__ import annotations

from .const import FAN_SPEED_MAX

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
