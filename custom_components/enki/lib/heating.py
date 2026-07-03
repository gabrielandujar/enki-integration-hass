"""Helpers for Enki heating / thermostat / pilot-wire capabilities."""

from __future__ import annotations

from typing import Any


def pilot_wire_options(possible_values: dict[str, Any]) -> list[str]:
    """Ordered pilot-wire modes from referentiel possibleValues."""
    meta = possible_values.get("switch_pilot_wire_mode") or possible_values.get(
        "check_pilot_wire_state"
    )
    if isinstance(meta, dict):
        values = meta.get("values")
        if isinstance(values, list):
            return [str(value) for value in values if isinstance(value, str)]
    return ["COMFORT", "COMFORT_1", "COMFORT_2", "ECO", "FROST_PROTECTION", "OFF"]


def thermostat_temperature_range(possible_values: dict[str, Any]) -> tuple[float, float, float]:
    """Return (min, max, step) for change_thermostat_target_temperature."""
    meta = possible_values.get("change_thermostat_target_temperature")
    if isinstance(meta, dict):
        range_meta = meta.get("range")
        if isinstance(range_meta, dict):
            minimum = range_meta.get("min")
            maximum = range_meta.get("max")
            step = range_meta.get("step")
            if isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)):
                resolved_step = float(step) if isinstance(step, (int, float)) else 0.5
                return float(minimum), float(maximum), resolved_step
    return 7.0, 28.0, 0.5


def thermostat_running_to_hvac_action(running_state: str | None) -> str | None:
    """Map Enki thermostat running state to Home Assistant hvac_action strings."""
    if not isinstance(running_state, str):
        return None
    normalized = running_state.upper()
    if normalized == "HEAT":
        return "heating"
    if normalized == "IDLE":
        return "idle"
    if normalized == "COOL":
        return "cooling"
    return None


def enabled_mode_is_on(value: str | None) -> bool | None:
    """Map ENABLED/DISABLED heating feature toggles to bool."""
    if not isinstance(value, str):
        return None
    normalized = value.upper()
    if normalized == "ENABLED":
        return True
    if normalized == "DISABLED":
        return False
    return None
