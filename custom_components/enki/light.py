"""Light platform for Enki lights, fan kits, switches and multi-endpoint nodes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.components.light.const import DEFAULT_MAX_KELVIN, DEFAULT_MIN_KELVIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import EnkiCoordinator
from .domain.models import EnkiDevice
from .entity import EnkiEntity
from .platforms.light.behavior import EnkiLightBehaviorMixin


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EnkiCoordinator = entry.runtime_data
    entities: list[LightEntity] = []
    for device in coordinator.data or []:
        entities.extend(_build_light_entities(coordinator, device))
    async_add_entities(entities)


def _build_light_entities(
    coordinator: EnkiCoordinator,
    device: EnkiDevice,
) -> list[LightEntity]:
    profile = device.profile
    if not profile.is_light_controllable:
        return []

    if profile.is_fan:
        return [EnkiFanLightEntity(coordinator, device)]

    endpoint_ids = profile.power_switch_endpoints
    if endpoint_ids:
        return [
            EnkiLightEntity(
                coordinator,
                device,
                suffix=f"light_{chr(ord('a') + index)}",
                endpoint_id=endpoint_id,
            )
            for index, endpoint_id in enumerate(endpoint_ids)
        ]

    translation_key = "outlet" if profile.uses_power_api_only else "light"
    return [EnkiLightEntity(coordinator, device, suffix="light", translation_key=translation_key)]


class EnkiFanLightEntity(EnkiLightBehaviorMixin, EnkiEntity, LightEntity):
    """Light kit on an ESDK ceiling fan (api-enki-lighting-prod)."""

    _attr_translation_key = "fan_light"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2748
    _attr_max_color_temp_kelvin = 6500
    _brightness_max = 100
    _color_temp_values: list[int] = []

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-light"
        possible = device.profile.possible_values
        self._brightness_max = self._parse_brightness_max(possible)
        self._color_temp_values = self._parse_color_temp_values(possible)

    @property
    def is_on(self) -> bool:
        return self._device.reported.light_power == "ON"

    @property
    def brightness(self) -> int | None:
        raw = self._device.reported.brightness
        return round(raw * 255 / self._brightness_max) if raw is not None else None

    @property
    def color_temp_kelvin(self) -> int | None:
        raw = self._device.reported.color_temperature
        return int(raw.strip("TK")) if raw else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._mixed_endpoint_workaround()
        changes = self._build_turn_on_changes(kwargs, restore_last_brightness=True)
        await self.coordinator.api.async_change_light_state(
            self._device.home_id,
            self._device.node_id,
            changes,
        )
        self._cache_global_light_on(self.coordinator)
        if "brightness" in changes:
            self.coordinator.update_cached_value(self.node_id, "brightness", changes["brightness"])
        if "colorTemperature" in changes:
            self.coordinator.update_cached_value(
                self.node_id,
                "colorTemperature",
                changes["colorTemperature"],
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_change_light_state(
            self._device.home_id,
            self._device.node_id,
            {"power": "OFF"},
        )
        self._cache_global_light_off(self.coordinator)


class EnkiLightEntity(EnkiLightBehaviorMixin, EnkiEntity, LightEntity):
    """Standard Enki light, dimmer, or switch/outlet node."""

    _attr_translation_key = "light"
    _brightness_max = 100
    _color_temp_values: list[int] = []

    def __init__(
        self,
        coordinator: EnkiCoordinator,
        device: EnkiDevice,
        *,
        suffix: str,
        endpoint_id: int | None = None,
        translation_key: str = "light",
    ) -> None:
        super().__init__(coordinator, device)
        self._endpoint_id = endpoint_id
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-{suffix}"

        profile = device.profile
        caps = profile.capabilities
        possible = profile.possible_values
        self._supports_light_state = profile.supports_light_state
        modes: set[ColorMode] = set()

        if "change_color_temperature" in caps:
            modes.add(ColorMode.COLOR_TEMP)
            self._color_temp_values = self._parse_color_temp_values(possible)
            if self._color_temp_values:
                self._attr_min_color_temp_kelvin = min(self._color_temp_values)
                self._attr_max_color_temp_kelvin = max(self._color_temp_values)
            else:
                self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
                self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

        if "change_brightness" in caps:
            modes.add(ColorMode.BRIGHTNESS)
            self._brightness_max = self._parse_brightness_max(possible)

        if not modes and profile.supports_electrical_power:
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
        reported = self._device.reported
        if self._endpoint_id is not None:
            power = reported.endpoint_power(self._endpoint_id)
            return power == "ON" if power is not None else False

        if reported.global_power is not None:
            return reported.global_power == "ON"

        return reported.electrical_power == "ON"

    @property
    def brightness(self) -> int | None:
        raw = self._device.reported.brightness
        if raw is None:
            return None
        return round(raw * 255 / self._brightness_max)

    @property
    def color_temp_kelvin(self) -> int | None:
        raw = self._device.reported.color_temperature
        return int(raw.strip("TK")) if raw else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id

        if not self._supports_light_state:
            await self.coordinator.api.async_switch_electrical_power(home_id, node_id, "ON")
            self.coordinator.update_cached_value(node_id, "electrical_power", "ON")
            return

        await self._mixed_endpoint_workaround()
        changes = self._build_turn_on_changes(kwargs)
        await self.coordinator.api.async_change_light_state(home_id, node_id, changes)
        self.coordinator.update_cached_value(node_id, "power", "ON")
        if "brightness" in changes:
            self.coordinator.update_cached_value(node_id, "brightness", changes["brightness"])
        if "colorTemperature" in changes:
            self.coordinator.update_cached_value(
                node_id,
                "colorTemperature",
                changes["colorTemperature"],
            )
        self._update_light_endpoint_cache("ON")

    async def async_turn_off(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id

        if not self._supports_light_state:
            await self.coordinator.api.async_switch_electrical_power(home_id, node_id, "OFF")
            self.coordinator.update_cached_value(node_id, "electrical_power", "OFF")
            return

        await self.coordinator.api.async_change_light_state(
            home_id,
            node_id,
            {"power": "OFF"},
        )
        self.coordinator.update_cached_value(node_id, "power", "OFF")
        self._update_light_endpoint_cache("OFF")
