"""Fan platform for Enki ceiling fans (Inspire Siroco+, etc.)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import (
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DEVICE_TYPE_FANS, DOMAIN, FAN_SPEED_MAX, ORDERED_FAN_SPEEDS
from .coordinator import EnkiCoordinator
from .entity import EnkiEntity
from .fan_helpers import (
    airflow_modes_from_metadata,
    enki_airflow_mode_to_preset,
    infer_airflow_mode_supported,
    preset_to_enki_airflow_mode,
)
from .fan_rotation_helpers import device_supports_fan_rotation
from .models import EnkiDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnkiCoordinator = entry.runtime_data
    async_add_entities(
        EnkiFanEntity(coordinator, device)
        for device in coordinator.data or []
        if device.device_type == DEVICE_TYPE_FANS
    )


class EnkiFanEntity(EnkiEntity, FanEntity):
    """Ceiling fan motor controlled via api-enki-airflow-prod."""

    _attr_translation_key = "ceiling_fan"

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-fan"
        self._preset_modes = airflow_modes_from_metadata(device)

    @property
    def supported_features(self) -> FanEntityFeature:
        features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._supports_direction():
            features |= FanEntityFeature.DIRECTION
        if self._supports_preset_mode():
            features |= FanEntityFeature.PRESET_MODE
        return features

    @property
    def preset_modes(self) -> list[str] | None:
        if not self._supports_preset_mode():
            return None
        return self._preset_modes

    @property
    def preset_mode(self) -> str | None:
        if not self._supports_preset_mode():
            return None
        return enki_airflow_mode_to_preset(self._device.last_reported_value.get("airflow_mode"))

    @property
    def is_on(self) -> bool:
        return self._device.last_reported_value.get("fan_speed", 0) > 0

    @property
    def percentage(self) -> int | None:
        speed = self._device.last_reported_value.get("fan_speed", 0)
        if speed <= 0:
            return 0
        return ordered_list_item_to_percentage(ORDERED_FAN_SPEEDS, speed)

    @property
    def speed_count(self) -> int:
        """Six discrete speeds; HA UI shows a stepped slider (≈17 % per step)."""
        return FAN_SPEED_MAX

    @property
    def current_direction(self) -> str | None:
        """forward = été (brise descendante), reverse = hiver (déstratification)."""
        return self._device.last_reported_value.get("airflow_rotation")

    async def async_set_direction(self, direction: str) -> None:
        if direction not in {DIRECTION_FORWARD, DIRECTION_REVERSE}:
            return
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_set_fan_rotation(home_id, node_id, direction)
        self.coordinator.update_cached_value(node_id, "airflow_rotation", direction)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if not self._supports_preset_mode():
            return
        if preset_mode not in self._preset_modes:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        home_id = self._device.home_id
        node_id = self._device.node_id
        enki_mode = preset_to_enki_airflow_mode(preset_mode)
        await self.coordinator.api.async_set_airflow_mode(home_id, node_id, enki_mode)
        self.coordinator.update_cached_value(node_id, "airflow_mode", enki_mode)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if preset_mode is not None and self._supports_preset_mode():
            await self.async_set_preset_mode(preset_mode)

        if percentage is not None and percentage > 0:
            speed = percentage_to_ordered_list_item(ORDERED_FAN_SPEEDS, percentage)
        else:
            speed = max(1, self._device.last_reported_value.get("fan_speed", 0) or 1)
        await self._set_speed(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_speed(0)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        await self._set_speed(percentage_to_ordered_list_item(ORDERED_FAN_SPEEDS, percentage))

    async def _set_speed(self, speed: int) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_set_fan_speed(home_id, node_id, speed)
        self.coordinator.update_cached_value(node_id, "fan_speed", speed)

    def _supports_direction(self) -> bool:
        if self._device.last_reported_value.get("airflow_rotation_supported"):
            return True
        return device_supports_fan_rotation(self._device)

    def _supports_preset_mode(self) -> bool:
        return infer_airflow_mode_supported(
            self._device,
            self._device.last_reported_value.get("airflow_mode"),
        )
