"""BFF dashboard field parsers (pure Python)."""

from __future__ import annotations

from typing import Any


def parse_bff_power(description: dict[str, Any] | None) -> float | None:
    """Parse power production from BFF description.value (e.g. '109 W' -> 109.0)."""
    if not description or not isinstance(description, dict):
        return None
    value_str = description.get("value")
    if not isinstance(value_str, str):
        return None
    try:
        return float(value_str.split()[0])
    except (ValueError, IndexError):
        return None
