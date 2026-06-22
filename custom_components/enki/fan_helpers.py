"""Fan preset / airflow mode helpers (no Home Assistant imports)."""

from __future__ import annotations

from typing import Any

from .const import (
    AIRFLOW_MODE_BREEZE,
    AIRFLOW_MODE_MANUAL,
    PRESET_MODE_BREEZE,
    PRESET_MODE_MANUAL,
)
from .models import EnkiDevice


def _capability_set(device: EnkiDevice) -> set[str]:
    return {capability for capability in device.capabilities if isinstance(capability, str)}


def _possible_values(device: EnkiDevice) -> dict[str, Any]:
    return device.possible_values if isinstance(device.possible_values, dict) else {}


def device_supports_airflow_mode(device: EnkiDevice) -> bool:
    capabilities = _capability_set(device)
    possible = _possible_values(device)
    return (
        "change_airflow_mode" in capabilities
        or "check_airflow_mode" in capabilities
        or "change_airflow_mode" in possible
        or "check_airflow_mode" in possible
    )


def airflow_modes_from_metadata(device: EnkiDevice) -> list[str]:
    possible = _possible_values(device)
    meta = possible.get("change_airflow_mode") or possible.get("check_airflow_mode")
    if isinstance(meta, dict):
        values = meta.get("values")
        if isinstance(values, list):
            presets: list[str] = []
            for value in values:
                preset = enki_airflow_mode_to_preset(str(value))
                if preset is not None and preset not in presets:
                    presets.append(preset)
            if presets:
                return presets
    return [PRESET_MODE_MANUAL, PRESET_MODE_BREEZE]


def enki_airflow_mode_to_preset(mode: str | None) -> str | None:
    if mode is None:
        return None
    normalized = mode.strip().upper()
    if normalized == AIRFLOW_MODE_MANUAL:
        return PRESET_MODE_MANUAL
    if normalized == AIRFLOW_MODE_BREEZE:
        return PRESET_MODE_BREEZE
    return None


def preset_to_enki_airflow_mode(preset: str) -> str:
    normalized = preset.strip().lower()
    if normalized == PRESET_MODE_MANUAL:
        return AIRFLOW_MODE_MANUAL
    if normalized == PRESET_MODE_BREEZE:
        return AIRFLOW_MODE_BREEZE
    raise ValueError(f"Unsupported preset mode: {preset}")


def infer_airflow_mode_supported(device: EnkiDevice, mode: str | None) -> bool:
    if enki_airflow_mode_to_preset(mode) is not None:
        return True
    return device_supports_airflow_mode(device)
