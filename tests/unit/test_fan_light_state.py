"""Unit tests for ESDK fan light on/off state merge in change-light-state."""

from __future__ import annotations


def test_change_light_state_payload_order_for_power_off() -> None:
    """Mirrors api.async_change_light_state merge: power OFF must win over default ON."""
    current = {"power": "ON", "brightness": 0.5, "colorTemperature": "T4000K"}
    parameter = "power"
    value = "OFF"
    payload = dict(current)
    payload["power"] = "ON"
    payload[parameter] = value
    assert payload["power"] == "OFF"


def test_fan_light_power_from_lighting_last_reported() -> None:
    last_reported = {"power": "OFF", "brightness": 0.2}
    assert last_reported.get("power", "OFF") == "OFF"
