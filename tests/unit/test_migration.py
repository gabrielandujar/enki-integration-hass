"""Unit tests for legacy config entry migration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from enki.const import CONF_SCAN_INTERVAL
from enki.migration import (
    migrate_config_entry_fields,
    migrate_legacy_entity_unique_ids,
    migrate_power_sensor_unique_id,
    resolve_scan_interval,
)


def test_migrate_config_entry_moves_scan_interval_to_options() -> None:
    data, options, unique_id = migrate_config_entry_fields(
        data={"username": "user@example.com", "password": "secret", CONF_SCAN_INTERVAL: 60},
        options={},
        unique_id="Enki - user@example.com",
    )

    assert CONF_SCAN_INTERVAL not in data
    assert options[CONF_SCAN_INTERVAL] == 60
    assert unique_id == "user@example.com"


def test_migrate_config_entry_keeps_existing_options() -> None:
    data, options, _unique_id = migrate_config_entry_fields(
        data={"username": "user@example.com", "password": "secret", CONF_SCAN_INTERVAL: 45},
        options={CONF_SCAN_INTERVAL: 30},
        unique_id="user@example.com",
    )

    assert options[CONF_SCAN_INTERVAL] == 30


def test_migrate_power_sensor_unique_id() -> None:
    assert (
        migrate_power_sensor_unique_id("enki-abc123-power_production")
        == "enki-abc123-power-production"
    )
    assert migrate_power_sensor_unique_id("enki-abc123-power-production") is None


def test_migrate_legacy_entity_unique_ids() -> None:
    registry = MagicMock()
    entity = MagicMock(
        entity_id="sensor.solar_power",
        unique_id="enki-node1-power_production",
    )

    with patch(
        "enki.migration.er.async_entries_for_config_entry",
        return_value=[entity],
    ):
        migrate_legacy_entity_unique_ids(registry, "entry-1")

    registry.async_update_entity.assert_called_once_with(
        "sensor.solar_power",
        new_unique_id="enki-node1-power-production",
    )


def test_resolve_scan_interval_prefers_options() -> None:
    entry = MagicMock()
    entry.options = {CONF_SCAN_INTERVAL: 45}
    entry.data = {CONF_SCAN_INTERVAL: 60}

    assert resolve_scan_interval(entry) == 45


def test_resolve_scan_interval_falls_back_to_legacy_data() -> None:
    entry = MagicMock()
    entry.options = {}
    entry.data = {CONF_SCAN_INTERVAL: 60}

    assert resolve_scan_interval(entry) == 60
