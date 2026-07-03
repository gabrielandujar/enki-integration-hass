"""Unit tests for fan preset / airflow mode helpers."""

from __future__ import annotations

from enki.const import PRESET_MODE_BREEZE, PRESET_MODE_MANUAL
from enki.fan_helpers import (
    airflow_modes_from_metadata,
    device_supports_airflow_mode,
    enki_airflow_mode_to_preset,
    infer_airflow_mode_supported,
    preset_to_enki_airflow_mode,
)
from enki.models import EnkiDevice


def test_airflow_mode_preset_mapping() -> None:
    assert enki_airflow_mode_to_preset("MANUAL") == PRESET_MODE_MANUAL
    assert enki_airflow_mode_to_preset("BREEZE") == PRESET_MODE_BREEZE
    assert preset_to_enki_airflow_mode(PRESET_MODE_BREEZE) == "BREEZE"


def test_infer_airflow_mode_supported_from_live_mode() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
    )
    assert infer_airflow_mode_supported(device, "BREEZE") is True


def test_device_supports_airflow_mode_from_capabilities() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
        capabilities=["change_airflow_mode"],
    )
    assert device_supports_airflow_mode(device) is True
    assert infer_airflow_mode_supported(device, None) is True


def test_airflow_modes_from_metadata_uses_referentiel_values() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
        possible_values={
            "change_airflow_mode": {"values": ["MANUAL", "BREEZE"]},
        },
    )
    assert airflow_modes_from_metadata(device) == ["MANUAL", "BREEZE"]
