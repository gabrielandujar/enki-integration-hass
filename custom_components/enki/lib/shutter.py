"""Shutter position helpers (pure Python)."""

from __future__ import annotations


def normalize_shutter_position(value: object) -> int | None:
    """Convert Enki shutter position to an HA cover percentage (0 = closed, 100 = open)."""
    if isinstance(value, bool):
        return 100 if value else 0
    if isinstance(value, int):
        return max(0, min(100, value))
    if isinstance(value, float):
        return max(0, min(100, int(round(value))))
    return None


def shutter_opening_is_closed(value: object) -> bool | None:
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized == "CLOSED":
            return True
        if normalized == "OPEN":
            return False
    return None
