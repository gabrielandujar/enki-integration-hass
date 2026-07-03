"""Light platform for Enki lights, fan kits, switches and multi-endpoint nodes."""

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

from .capabilities import capabilities_set as device_capabilities_set
from .capabilities import (
    device_uses_power_api_only,
    is_fan_device,
    is_light_controllable,
    main_change_capability_endpoints,
    supports_light_state,
)
from .capabilities import possible_values_dict as device_possible_values
from .const import DOMAIN
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
        entities.extend(_build_light_entities(coordinator, device))
    async_add_entities(entities)


def _build_light_entities(
    coordinator: EnkiCoordinator,
    device: EnkiDevice,
) -> list[LightEntity]:
    if not is_light_controllable(device):
        return []

    if is_fan_device(device):
        return [EnkiFanLightEntity(coordinator, device)]

    endpoint_ids = main_change_capability_endpoints(device)
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

    translation_key = "outlet" if device_uses_power_api_only(device) else "light"
    return [EnkiLightEntity(coordinator, device, suffix="light", translation_key=translation_key)]


class EnkiFanLightEntity(EnkiEntity, LightEntity):
    """Light kit on an ESDK ceiling fan (api-enki-lighting-prod)."""

    _attr_translation_key = "fan_light"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2748
    _attr_max_color_temp_kelvin = 6500
    _brightness_max = 100

    def __init__(self, coordinator: EnkiCoordinator, device: EnkiDevice) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-light"
        possible = device_possible_values(device.possible_values)
        brightness_range = possible.get("change_brightness", {}).get("range", {})
        self._brightness_max = brightness_range.get("max", 100)
        values = possible.get("change_color_temperature", {}).get("values", [])
        if values:
            self._color_temp_values = [int(value.strip("TK")) for value in values]
        else:
            self._color_temp_values = []

    @property
    def is_on(self) -> bool:
        return self._device.last_reported_value.get("light_power") == "ON"

    @property
    def brightness(self) -> int | None:
        raw = self._device.last_reported_value.get("brightness")
        return round(raw * 255 / self._brightness_max) if raw is not None else None

    @property
    def color_temp_kelvin(self) -> int | None:
        raw = self._device.last_reported_value.get("colorTemperature")
        return int(raw.strip("TK")) if raw else None

    def _closest_color_temp(self, target: int) -> str:
        best = min(self._color_temp_values, key=lambda value: abs(value - target))
        return f"T{best}K"

    def _light_endpoints_have_mixed_power(self) -> bool:
        endpoint_ids = main_change_capability_endpoints(self._device)
        if len(endpoint_ids) <= 1:
            return False
        endpoints = self._device.last_reported_value.get("electrical_endpoints")
        if not isinstance(endpoints, list):
            return False
        power_values: set[str] = set()
        for endpoint in endpoints:
            if not isinstance(endpoint, dict) or endpoint.get("id") not in endpoint_ids:
                continue
            last_reported = endpoint.get("lastReportedValue")
            if isinstance(last_reported, str) and last_reported in {"ON", "OFF"}:
                power_values.add(last_reported)
            if len(power_values) > 1:
                return True
        return False

    async def _mixed_endpoint_workaround(self) -> None:
        if self._light_endpoints_have_mixed_power():
            await self.coordinator.api.async_change_light_state(
                self._device.home_id,
                self._device.node_id,
                {"power": "OFF"},
            )

    def _build_turn_on_changes(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        changes: dict[str, Any] = {"power": "ON"}
        if ATTR_BRIGHTNESS in kwargs:
            changes["brightness"] = round(
                kwargs[ATTR_BRIGHTNESS] * self._brightness_max / 255,
                2,
            )
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            if self._color_temp_values:
                changes["colorTemperature"] = self._closest_color_temp(
                    kwargs[ATTR_COLOR_TEMP_KELVIN]
                )
            else:
                changes["colorTemperature"] = f"T{kwargs[ATTR_COLOR_TEMP_KELVIN]}K"
        elif ATTR_BRIGHTNESS not in kwargs:
            last_brightness = self._device.last_reported_value.get("brightness")
            if isinstance(last_brightness, (int, float)) and last_brightness > 0:
                changes["brightness"] = last_brightness
        return changes

    async def async_turn_on(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self._mixed_endpoint_workaround()
        changes = self._build_turn_on_changes(kwargs)
        await self.coordinator.api.async_change_light_state(home_id, node_id, changes)
        self._apply_light_cache(node_id, changes)

    async def async_turn_off(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id
        await self.coordinator.api.async_change_light_state(
            home_id,
            node_id,
            {"power": "OFF"},
        )
        self._cache_light_off(node_id)

    def _apply_light_cache(self, node_id: str, changes: dict[str, Any]) -> None:
        self._cache_light_on(node_id)
        if "brightness" in changes:
            self.coordinator.update_cached_value(node_id, "brightness", changes["brightness"])
        if "colorTemperature" in changes:
            self.coordinator.update_cached_value(
                node_id,
                "colorTemperature",
                changes["colorTemperature"],
            )

    def _cache_light_on(self, node_id: str) -> None:
        self.coordinator.update_cached_value(node_id, "light_power", "ON")
        self.coordinator.update_cached_value(node_id, "power", "ON")

    def _cache_light_off(self, node_id: str) -> None:
        self.coordinator.update_cached_value(node_id, "light_power", "OFF")
        self.coordinator.update_cached_value(node_id, "power", "OFF")


class EnkiLightEntity(EnkiEntity, LightEntity):
    """Standard Enki light, dimmer, or switch/outlet node."""

    _attr_translation_key = "light"
    _brightness_max = 100

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
        self._color_temp_values: list[int] = []
        caps = device_capabilities_set(device.capabilities)
        possible = device_possible_values(device.possible_values)
        self._supports_light_state = supports_light_state(caps, possible)
        modes: set[ColorMode] = set()

        if "change_color_temperature" in caps:
            modes.add(ColorMode.COLOR_TEMP)
            values = possible.get("change_color_temperature", {}).get("values", [])
            if values:
                self._color_temp_values = [int(value.strip("TK")) for value in values]
                self._attr_min_color_temp_kelvin = min(self._color_temp_values)
                self._attr_max_color_temp_kelvin = max(self._color_temp_values)
            else:
                self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
                self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

        if "change_brightness" in caps:
            modes.add(ColorMode.BRIGHTNESS)
            brightness_range = possible.get("change_brightness", {}).get("range", {})
            self._brightness_max = brightness_range.get("max", 100)

        if not modes and "switch_electrical_power" in caps:
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
        if self._endpoint_id is not None:
            endpoints = self._device.last_reported_value.get("electrical_endpoints")
            if isinstance(endpoints, list):
                for endpoint in endpoints:
                    if not isinstance(endpoint, dict):
                        continue
                    if endpoint.get("id") != self._endpoint_id:
                        continue
                    last_reported = endpoint.get("lastReportedValue")
                    if isinstance(last_reported, str):
                        return last_reported == "ON"
                    if isinstance(last_reported, dict):
                        power = last_reported.get("power")
                        return power == "ON" if power is not None else None

        power = self._device.last_reported_value.get("power")
        if power is not None:
            return power == "ON"

        electrical_power = self._device.last_reported_value.get("electrical_power")
        return isinstance(electrical_power, str) and electrical_power == "ON"

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

    def _light_endpoint_ids(self) -> list[int]:
        return main_change_capability_endpoints(self._device)

    def _light_endpoints_have_mixed_power(self) -> bool:
        endpoint_ids = self._light_endpoint_ids()
        if len(endpoint_ids) <= 1:
            return False

        endpoints = self._device.last_reported_value.get("electrical_endpoints")
        if not isinstance(endpoints, list):
            return False

        power_values: set[str] = set()
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            if endpoint.get("id") not in endpoint_ids:
                continue
            last_reported = endpoint.get("lastReportedValue")
            if isinstance(last_reported, str) and last_reported in {"ON", "OFF"}:
                power_values.add(last_reported)
            elif isinstance(last_reported, dict):
                power = last_reported.get("power")
                if power in {"ON", "OFF"}:
                    power_values.add(power)
            if len(power_values) > 1:
                return True
        return False

    def _update_light_endpoint_cache(self, power: str) -> None:
        for endpoint_id in self._light_endpoint_ids():
            self.coordinator.update_endpoint_power(self._device.node_id, endpoint_id, power)

    async def _mixed_endpoint_workaround(self) -> None:
        if self._light_endpoints_have_mixed_power():
            await self.coordinator.api.async_change_light_state(
                self._device.home_id,
                self._device.node_id,
                {"power": "OFF"},
            )

    def _build_turn_on_changes(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        changes: dict[str, Any] = {"power": "ON"}
        if ATTR_BRIGHTNESS in kwargs:
            changes["brightness"] = round(
                kwargs[ATTR_BRIGHTNESS] * self._brightness_max / 255,
                2,
            )
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            if self._color_temp_values:
                changes["colorTemperature"] = self._closest_color_temp(
                    kwargs[ATTR_COLOR_TEMP_KELVIN]
                )
            else:
                changes["colorTemperature"] = f"T{kwargs[ATTR_COLOR_TEMP_KELVIN]}K"
        return changes

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
