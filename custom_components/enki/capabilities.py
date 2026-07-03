"""Capability-based Enki device detection (referentiel + BFF metadata)."""

from __future__ import annotations

from typing import Any

from .const import DEVICE_TYPE_FANS, DEVICE_TYPE_INVERTERS, DEVICE_TYPE_LIGHTS
from .models import EnkiDevice


def capabilities_set(capabilities: list[str] | dict[str, Any] | None) -> set[str]:
    """Normalize referentiel capabilities to a string set."""
    if isinstance(capabilities, list):
        return {capability for capability in capabilities if isinstance(capability, str)}
    if isinstance(capabilities, dict):
        return set(capabilities.keys())
    return set()


def possible_values_dict(possible_values: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(possible_values, dict):
        return possible_values
    return {}


def supports_light_state(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return (
        "change_light_state" in capabilities
        or "check_light_state" in capabilities
        or "change_light_state" in possible_values
        or "check_light_state" in possible_values
    )


def supports_electrical_power(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return (
        "switch_electrical_power" in capabilities
        or "check_electrical_power" in capabilities
        or "switch_electrical_power" in possible_values
        or "check_electrical_power" in possible_values
    )


def supports_fan_speed(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return (
        "change_fan_speed" in capabilities
        or "check_fan_speed" in capabilities
        or "change_fan_speed" in possible_values
        or "check_fan_speed" in possible_values
    )


def supports_fan_rotation(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return (
        "change_fan_rotation_direction" in capabilities
        or "check_fan_rotation_direction" in capabilities
        or "change_fan_rotation_direction" in possible_values
        or "check_fan_rotation_direction" in possible_values
    )


def supports_airflow_mode(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return (
        "change_airflow_mode" in capabilities
        or "check_airflow_mode" in capabilities
        or "change_airflow_mode" in possible_values
        or "check_airflow_mode" in possible_values
    )


def supports_power_production(capabilities: set[str]) -> bool:
    return "check_power_production" in capabilities


def device_capabilities(device: EnkiDevice) -> set[str]:
    return capabilities_set(device.capabilities)


def device_possible_values(device: EnkiDevice) -> dict[str, Any]:
    return possible_values_dict(device.possible_values)


def is_fan_device(device: EnkiDevice) -> bool:
    """Detect fans from capabilities (Inspire, Cadix, Radix, VMC, …)."""
    if device.device_type == DEVICE_TYPE_FANS:
        return True
    caps = device_capabilities(device)
    possible = device_possible_values(device)
    return (
        supports_fan_speed(caps, possible)
        or supports_fan_rotation(caps, possible)
        or supports_airflow_mode(caps, possible)
    )


def is_light_controllable(device: EnkiDevice) -> bool:
    """Lights, dimmers, and switch/outlet nodes exposed as HA lights."""
    if device.device_type == DEVICE_TYPE_LIGHTS:
        return True
    caps = device_capabilities(device)
    possible = device_possible_values(device)
    if is_fan_device(device):
        return supports_light_state(caps, possible)
    return supports_light_state(caps, possible) or supports_electrical_power(caps, possible)


def is_inverter_device(device: EnkiDevice) -> bool:
    """Solar inverters reporting live production via the BFF dashboard."""
    if device.device_type in {DEVICE_TYPE_INVERTERS, "inverters"}:
        return device.power_production is not None
    caps = device_capabilities(device)
    return supports_power_production(caps) and device.power_production is not None


def device_is_supported(device: EnkiDevice) -> bool:
    return is_fan_device(device) or is_light_controllable(device) or is_inverter_device(device)


def device_uses_power_api_only(device: EnkiDevice) -> bool:
    """Pure switches/outlets (e.g. Edisio) without the lighting API."""
    caps = device_capabilities(device)
    possible = device_possible_values(device)
    return supports_electrical_power(caps, possible) and not supports_light_state(caps, possible)


def fan_max_speed(device: EnkiDevice) -> int | None:
    """Read max fan speed from referentiel possibleValues."""
    possible = device_possible_values(device)
    speed_meta = possible.get("change_fan_speed") or possible.get("check_fan_speed")
    if isinstance(speed_meta, dict):
        speed_range = speed_meta.get("range")
        if isinstance(speed_range, dict):
            raw_max = speed_range.get("max")
            if isinstance(raw_max, (int, float)) and raw_max > 0:
                return max(1, int(round(raw_max)))
    return None


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


def main_change_capability_endpoints(device: EnkiDevice) -> list[int]:
    """Return BFF endpoints for mainChangeCapability=switch_electrical_power."""
    if device.main_change_capability_id != "switch_electrical_power":
        return []

    endpoint_ids: set[int] = set()
    for endpoint in device.main_change_capability_endpoints:
        if isinstance(endpoint, int):
            endpoint_ids.add(endpoint)
        elif isinstance(endpoint, dict):
            endpoint_id = endpoint.get("id")
            if isinstance(endpoint_id, int):
                endpoint_ids.add(endpoint_id)

    return sorted(endpoint_ids)
