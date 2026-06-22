"""Fan rotation capability helpers (no Home Assistant imports)."""

from __future__ import annotations

from typing import Any

from .models import EnkiDevice


def _capability_set(device: EnkiDevice) -> set[str]:
    return {capability for capability in device.capabilities if isinstance(capability, str)}


def _possible_values(device: EnkiDevice) -> dict[str, Any]:
    return device.possible_values if isinstance(device.possible_values, dict) else {}


def device_supports_fan_rotation(device: EnkiDevice) -> bool:
    capabilities = _capability_set(device)
    possible = _possible_values(device)
    return (
        "change_fan_rotation_direction" in capabilities
        or "check_fan_rotation_direction" in capabilities
        or "change_fan_rotation_direction" in possible
        or "check_fan_rotation_direction" in possible
    )
