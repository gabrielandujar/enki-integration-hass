"""Fan rotation capability helpers (no Home Assistant imports)."""

from __future__ import annotations

from .models import EnkiDevice


def device_supports_fan_rotation(device: EnkiDevice) -> bool:
    return device.profile.supports_fan_rotation
