"""Light platform for Enki lights and fan light kits."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.components.light.const import DEFAULT_MAX_KELVIN, DEFAULT_MIN_KELVIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_FANS, DEVICE_TYPE_LIGHTS, DOMAIN
from .coordinator import EnkiCoordinator
from .entity import EnkiEntity
from .models import EnkiDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnkiCoordinator = entry.runtime_data
    entities: list[LightEntity] = []
    for device in coordinator.data or []:
        if device.device_type == DEVICE_TYPE_FANS:
            entities.append(EnkiFanLightEntity(coordinator, device))
        elif device.device_type == DEVICE_TYPE_LIGHTS:
            entities.append(EnkiLightEntity(coordinator, device))
    async_add_entities(entities)


class EnkiFanLightEntity(EnkiEntity, LightEntity):
    """Light kit on an ESDK ceiling fan (api-enki-lighting-prod)."""

    _attr_translation_key = "fan_light"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2748
    _attr_max_color_temp_kelvin = 6500

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-light"

    @property
    def is_on(self) -> bool:
        power = self._device.last_reported_value.get("light_power")
        if power is not None:
            return power == "ON"
        return self._device.last_reported_value.get("power") == "ON"

    @property
    def brightness(self) -> int | None:
        raw = self._device.last_reported_value.get("brightness")
        return round(raw * 255) if raw is not None else None

    @property
    def color_temp_kelvin(self) -> int | None:
        raw = self._device.last_reported_value.get("colorTemperature")
        return int(raw.strip("TK")) if raw else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        if ATTR_BRIGHTNESS in kwargs:
            value = round(kwargs[ATTR_BRIGHTNESS] / 255, 2)
            await self.coordinator.api.async_change_light_state(
                home_id, node_id, "brightness", value
            )
            self.coordinator.update_cached_value(node_id, "brightness", value)
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            value = f"T{kwargs[ATTR_COLOR_TEMP_KELVIN]}K"
            await self.coordinator.api.async_change_light_state(
                home_id, node_id, "colorTemperature", value
            )
            self.coordinator.update_cached_value(node_id, "colorTemperature", value)
        else:
            await self.coordinator.api.async_change_light_state(home_id, node_id, "power", "ON")
        self.coordinator.update_cached_value(node_id, "light_power", "ON")
        self.coordinator.update_cached_value(node_id, "power", "ON")

    async def async_turn_off(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_change_light_state(home_id, node_id, "power", "OFF")
        self.coordinator.update_cached_value(node_id, "light_power", "OFF")
        self.coordinator.update_cached_value(node_id, "power", "OFF")


class EnkiLightEntity(EnkiEntity, LightEntity):
    """Standard Enki light node."""

    _attr_translation_key = "light"
    _brightness_max = 100

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-light"
        self._color_temp_values: list[int] = []
        modes: set[ColorMode] = set()
        possible = device.possible_values
        capabilities = device.capabilities

        if "change_color_temperature" in capabilities:
            modes.add(ColorMode.COLOR_TEMP)
            values = possible.get("change_color_temperature", {}).get("values", [])
            if values:
                self._color_temp_values = [int(value.strip("TK")) for value in values]
                self._attr_min_color_temp_kelvin = min(self._color_temp_values)
                self._attr_max_color_temp_kelvin = max(self._color_temp_values)
            else:
                self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
                self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

        if "change_brightness" in capabilities:
            modes.add(ColorMode.BRIGHTNESS)
            brightness_range = possible.get("change_brightness", {}).get("range", {})
            self._brightness_max = brightness_range.get("max", 100)

        if not modes and "switch_electrical_power" in capabilities:
            modes.add(ColorMode.ONOFF)

        self._attr_supported_color_modes = modes or {ColorMode.ONOFF}
        if ColorMode.COLOR_TEMP in modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
        elif ColorMode.BRIGHTNESS in modes:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        return self._device.last_reported_value.get("power") == "ON"

    @property
    def brightness(self) -> int | None:
        raw = self._device.last_reported_value.get("brightness")
        if raw is None:
            return None
        return round(raw * 255 / self._brightness_max)

    @property
    def color_temp_kelvin(self) -> int | None:
        raw = self._device.last_reported_value.get("colorTemperature")
        return int(raw.strip("TK")) if raw else None

    def _closest_color_temp(self, target: int) -> str:
        best = min(self._color_temp_values, key=lambda value: abs(value - target))
        return f"T{best}K"

    async def async_turn_on(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        if ATTR_BRIGHTNESS in kwargs:
            value = round(kwargs[ATTR_BRIGHTNESS] * self._brightness_max / 255, 2)
            await self.coordinator.api.async_change_light_state(
                home_id, node_id, "brightness", value
            )
            self.coordinator.update_cached_value(node_id, "brightness", value)
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            if self._color_temp_values:
                value = self._closest_color_temp(kwargs[ATTR_COLOR_TEMP_KELVIN])
            else:
                value = f"T{kwargs[ATTR_COLOR_TEMP_KELVIN]}K"
            await self.coordinator.api.async_change_light_state(
                home_id, node_id, "colorTemperature", value
            )
            self.coordinator.update_cached_value(node_id, "colorTemperature", value)
        else:
            await self.coordinator.api.async_change_light_state(home_id, node_id, "power", "ON")
            self.coordinator.update_cached_value(node_id, "power", "ON")

    async def async_turn_off(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_change_light_state(home_id, node_id, "power", "OFF")
        self.coordinator.update_cached_value(node_id, "power", "OFF")
