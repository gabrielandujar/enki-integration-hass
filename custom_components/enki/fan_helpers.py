"""Fan preset / airflow mode helpers (no Home Assistant imports)."""

from __future__ import annotations

from .const import (
    AIRFLOW_MODE_BREEZE,
    AIRFLOW_MODE_MANUAL,
    PRESET_MODE_BREEZE,
    PRESET_MODE_MANUAL,
)
from .models import EnkiDevice


def device_supports_airflow_mode(device: EnkiDevice) -> bool:
    return device.profile.supports_airflow_mode


def airflow_modes_from_metadata(device: EnkiDevice) -> list[str]:
    possible = device.profile.possible_values
    meta = possible.get("change_airflow_mode") or possible.get("check_airflow_mode")
    if isinstance(meta, dict):
        values = meta.get("values")
        if isinstance(values, list):
            modes = [str(value) for value in values if isinstance(value, str)]
            if modes:
                return modes
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
    normalized = preset.strip().upper()
    if normalized in {
        "MANUAL",
        "BREEZE",
        "VENTILATION",
        "BOOST",
        "AUTO",
        "SLEEP",
    }:
        return normalized
    lowered = preset.strip().lower()
    if lowered == PRESET_MODE_MANUAL:
        return AIRFLOW_MODE_MANUAL
    if lowered == PRESET_MODE_BREEZE:
        return AIRFLOW_MODE_BREEZE
    raise ValueError(f"Unsupported preset mode: {preset}")


def infer_airflow_mode_supported(device: EnkiDevice, mode: str | None) -> bool:
    if mode is not None and mode in airflow_modes_from_metadata(device):
        return True
    if enki_airflow_mode_to_preset(mode) is not None:
        return True
    return device_supports_airflow_mode(device)
