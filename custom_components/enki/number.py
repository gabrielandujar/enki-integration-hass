"""Number platform for Enki contact sensor configuration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EnkiCoordinator
from .domain.models import EnkiDevice
from .entity import EnkiEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnkiCoordinator = entry.runtime_data
    async_add_entities(
        EnkiVibrationSensibilityNumber(coordinator, device)
        for device in coordinator.data or []
        if device.profile.supports_vibration_sensibility
    )


class EnkiVibrationSensibilityNumber(EnkiEntity, NumberEntity):
    """Vibration sensitivity level on Lexman contact sensors."""

    _attr_has_entity_name = True
    _attr_translation_key = "vibration_sensibility"
    _attr_native_min_value = 1
    _attr_native_max_value = 5
    _attr_native_step = 1

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-vibration-sensibility"

    @property
    def native_value(self) -> float | None:
        return self._device.reported.vibration_sensibility_level

    async def async_set_native_value(self, value: float) -> None:
        level = str(int(value))
        await self.coordinator.api.async_set_capability_value(
            self._device.home_id,
            self._device.node_id,
            "contact_sensor",
            "change_vibration_sensibility_level",
            level,
        )
        self.coordinator.update_cached_value(
            self.node_id,
            "vibration_sensibility_level",
            level,
        )
