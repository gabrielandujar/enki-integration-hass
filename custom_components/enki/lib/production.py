"""Solar production value parsers (BFF + Envertech API)."""

from __future__ import annotations

from typing import Any

from .bff import parse_bff_power


def parse_production_value(value: Any) -> float | None:
    """Normalize power (W) or energy (kWh) readings from Enki micro-services."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        parsed = parse_bff_power({"value": value})
        if parsed is not None:
            return parsed
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ("value", "lastReportedValue", "amount"):
            if key in value:
                parsed = parse_production_value(value[key])
                if parsed is not None:
                    return parsed
    return None
