"""Unit tests for GDANSK BLE routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from enki.api.client import EnkiAPI
from enki.domain.models import EnkiDevice
from enki.light import EnkiLightEntity


def _gdansk_device(**overrides) -> EnkiDevice:
    defaults = {
        "home_id": "home-1",
        "device_id": "gdansk-device",
        "node_id": "node-gdansk",
        "device_name": "GDANSK",
        "device_type": "lights",
        "is_enabled": True,
        "state": "ACTIVE",
        "capabilities": [
            "change_light_state",
            "check_light_state",
            "change_brightness",
            "change_color_temperature",
            "change_hue",
            "change_saturation",
        ],
        "possible_values": {
            "change_brightness": {"range": {"min": 1, "max": 100}},
            "change_color_temperature": {"values": ["T2700K", "T4000K", "T6500K"]},
        },
        "last_reported_value": {"eui64": "f082c049d7d2", "power": "OFF"},
        "referentiel_model": "ZBEK-29",
    }
    defaults.update(overrides)
    return EnkiDevice(**defaults)


def test_profile_detects_gdansk_ble() -> None:
    assert _gdansk_device().profile.is_gdansk_ble is True
    assert _gdansk_device(referentiel_model="OTHER").profile.is_gdansk_ble is False


@pytest.mark.asyncio
async def test_api_reads_gdansk_state_via_ble() -> None:
    api = EnkiAPI("user", "pass")
    api._async_fetch_gdansk_ble_state = AsyncMock(return_value={"power": "ON"})  # type: ignore[attr-defined]
    http = MagicMock()

    state = await api._read_light_payload(http, _gdansk_device())  # type: ignore[arg-type]

    assert state == {"power": "ON"}
    api._async_fetch_gdansk_ble_state.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_api_skips_cloud_change_for_gdansk() -> None:
    api = EnkiAPI("user", "pass")
    api._async_apply_gdansk_ble_state = AsyncMock(return_value={"power": "ON"})  # type: ignore[attr-defined]
    api._get_http = AsyncMock()

    await api.async_apply_gdansk_light_state(
        _gdansk_device(),
        power=True,
        brightness=128,
        color_temp_kelvin=4000,
        hs_color=(210, 80),
    )

    api._async_apply_gdansk_ble_state.assert_awaited_once()  # type: ignore[attr-defined]
    api._get_http.assert_not_awaited()


@pytest.mark.asyncio
async def test_light_entity_turn_on_routes_gdansk_to_ble() -> None:
    coordinator = MagicMock()
    coordinator.api.async_apply_gdansk_light_state = AsyncMock()
    coordinator.api.async_change_light_state = AsyncMock()
    coordinator.api.async_change_light_color = AsyncMock()
    coordinator.api.async_switch_electrical_power = AsyncMock()
    coordinator.update_cached_value = MagicMock()
    coordinator.update_endpoint_power = MagicMock()
    entity = EnkiLightEntity(coordinator, _gdansk_device(), suffix="light")

    await entity.async_turn_on(brightness=128, hs_color=(210, 80))

    coordinator.api.async_apply_gdansk_light_state.assert_awaited_once()
    coordinator.api.async_change_light_state.assert_not_called()
    coordinator.api.async_change_light_color.assert_not_called()


@pytest.mark.asyncio
async def test_light_entity_turn_off_routes_gdansk_to_ble() -> None:
    coordinator = MagicMock()
    coordinator.api.async_apply_gdansk_light_state = AsyncMock(return_value={"power": "OFF"})
    coordinator.api.async_change_light_state = AsyncMock()
    coordinator.update_cached_value = MagicMock()
    coordinator.update_endpoint_power = MagicMock()
    entity = EnkiLightEntity(coordinator, _gdansk_device(), suffix="light")

    await entity.async_turn_off()

    coordinator.api.async_apply_gdansk_light_state.assert_awaited_once_with(
        entity.device,
        power=False,
    )
    coordinator.api.async_change_light_state.assert_not_called()
