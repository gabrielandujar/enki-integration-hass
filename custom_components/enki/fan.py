"""Fan platform for Enki ceiling fans (Inspire Siroco+, Cadix, Radix, …)."""

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

from .const import DOMAIN, FAN_SPEED_MAX
from .coordinator import EnkiCoordinator
from .domain.models import EnkiDevice
from .entity import EnkiEntity
from .platforms.fan.airflow import (
    airflow_modes_from_metadata,
    device_supports_fan_rotation,
    enki_airflow_mode_to_preset,
    infer_airflow_mode_supported,
    preset_mode_icon,
    preset_to_enki_airflow_mode,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnkiCoordinator = entry.runtime_data
    async_add_entities(
        EnkiFanEntity(coordinator, device)
        for device in coordinator.data or []
        if device.profile.is_fan
    )


class EnkiFanEntity(EnkiEntity, FanEntity):
    """Ceiling fan motor controlled via api-enki-airflow-prod."""

    _attr_translation_key = "ceiling_fan"

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-fan"
        self._preset_modes = airflow_modes_from_metadata(device)
        self._ordered_speeds = self._build_ordered_speeds(device)

    def _build_ordered_speeds(self, device: EnkiDevice) -> list[int]:
        max_speed = device.profile.fan_max_speed or FAN_SPEED_MAX
        return list(range(1, max_speed + 1))

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
        slug = enki_airflow_mode_to_preset(self._device.reported.airflow_mode)
        if slug is not None and slug in self._preset_modes:
            return slug
        return None

    @property
    def icon(self) -> str:
        if (
            self._supports_preset_mode()
            and (preset := self.preset_mode)
            and (preset_icon := preset_mode_icon(preset))
        ):
            return preset_icon
        return "mdi:fan-ceiling"

    @property
    def is_on(self) -> bool:
        speed = self._device.reported.fan_speed
        if speed is not None:
            return speed > 0
        return self._device.reported.electrical_power == "ON"

    @property
    def percentage(self) -> int | None:
        speed = self._device.reported.fan_speed
        if speed is None:
            return None
        if speed <= 0:
            return 0
        return ordered_list_item_to_percentage(self._ordered_speeds, speed)

    @property
    def speed_count(self) -> int:
        return len(self._ordered_speeds)

    @property
    def current_direction(self) -> str | None:
        """forward = summer (downward breeze), reverse = winter (destratification)."""
        return self._device.reported.airflow_rotation

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

        if self._device.reported.fan_speed is None:
            if percentage is None or percentage > 0:
                await self.coordinator.api.async_switch_electrical_power(
                    self._device.home_id,
                    self._device.node_id,
                    "ON",
                )
                self.coordinator.update_cached_value(
                    self._device.node_id,
                    "electrical_power",
                    "ON",
                )
            return

        if percentage is not None and percentage > 0:
            speed = percentage_to_ordered_list_item(self._ordered_speeds, percentage)
        else:
            speed = max(1, self._device.reported.fan_speed or 1)
        await self._set_speed(speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._device.reported.fan_speed is None:
            await self.coordinator.api.async_switch_electrical_power(
                self._device.home_id,
                self._device.node_id,
                "OFF",
            )
            self.coordinator.update_cached_value(
                self._device.node_id,
                "electrical_power",
                "OFF",
            )
            return
        await self._set_speed(0)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        await self._set_speed(percentage_to_ordered_list_item(self._ordered_speeds, percentage))

    async def _set_speed(self, speed: int) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_set_fan_speed(home_id, node_id, speed)
        self.coordinator.update_cached_value(node_id, "fan_speed", speed)

    def _supports_direction(self) -> bool:
        if self._device.reported.airflow_rotation_supported:
            return True
        return device_supports_fan_rotation(self._device)

    def _supports_preset_mode(self) -> bool:
        return infer_airflow_mode_supported(
            self._device,
            self._device.reported.airflow_mode,
        )
