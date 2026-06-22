"""Unit tests for fan preset / airflow mode helpers."""

from __future__ import annotations

from enki.const import PRESET_MODE_BREEZE, PRESET_MODE_MANUAL
from enki.fan_helpers import (
    enki_airflow_mode_to_preset,
    preset_to_enki_airflow_mode,
)
from enki.models import EnkiDevice


def test_airflow_mode_preset_mapping() -> None:
    assert enki_airflow_mode_to_preset("MANUAL") == PRESET_MODE_MANUAL
    assert enki_airflow_mode_to_preset("BREEZE") == PRESET_MODE_BREEZE
    assert preset_to_enki_airflow_mode(PRESET_MODE_BREEZE) == "BREEZE"


def test_infer_airflow_mode_supported_from_live_mode() -> None:
    from enki.fan_helpers import infer_airflow_mode_supported

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
