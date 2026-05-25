"""Fan platform for Enki ceiling fans (Inspire Siroco+, etc.)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DEVICE_TYPE_FANS, DOMAIN, FAN_SPEED_MAX
from .coordinator import EnkiCoordinator
from .entity import EnkiEntity
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
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-fan"

    @property
    def is_on(self) -> bool:
        return self._device.last_reported_value.get("fan_speed", 0) > 0

    @property
    def percentage(self) -> int | None:
        speed = self._device.last_reported_value.get("fan_speed", 0)
        if speed <= 0:
            return 0
        return ordered_list_item_to_percentage(self.speed_count, speed)

    @property
    def speed_count(self) -> int:
        """Six discrete speeds; HA UI shows a stepped slider (≈17 % per step)."""
        return FAN_SPEED_MAX

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if percentage is not None and percentage > 0:
            speed = percentage_to_ordered_list_item(self.speed_count, percentage)
        else:
            speed = max(1, self._device.last_reported_value.get("fan_speed", 0) or 1)
        await self._set_speed(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_speed(0)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        await self._set_speed(percentage_to_ordered_list_item(self.speed_count, percentage))

    async def _set_speed(self, speed: int) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_set_fan_speed(home_id, node_id, speed)
        self.coordinator.update_cached_value(node_id, "fan_speed", speed)
