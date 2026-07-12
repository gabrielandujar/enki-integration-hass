"""Light platform for Enki lights, fan kits, switches and multi-endpoint nodes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.components.light.const import DEFAULT_MAX_KELVIN, DEFAULT_MIN_KELVIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import EnkiCoordinator
from .domain.models import EnkiDevice
from .entity import EnkiEntity
from .lib.conversion import enki_to_hs, hs_to_enki, select_light_color_modes
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
        light_endpoints = profile.fan_light_endpoints
        if len(light_endpoints) > 1:
            return [
                EnkiFanLightEntity(
                    coordinator,
                    device,
                    endpoint_id=endpoint_id,
                    suffix=f"light_{chr(ord('a') + index)}",
                )
                for index, endpoint_id in enumerate(light_endpoints)
            ]
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

    return [EnkiLightEntity(coordinator, device, suffix="light")]


class EnkiFanLightEntity(EnkiLightBehaviorMixin, EnkiEntity, LightEntity):
    """Light kit on an ESDK ceiling fan (api-enki-lighting-prod)."""

    _attr_translation_key = "fan_light"
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = 2748
    _attr_max_color_temp_kelvin = 6500
    _brightness_max = 100
    _color_temp_values: list[int] = []

    def __init__(
        self,
        coordinator: EnkiCoordinator,
        device: EnkiDevice,
        *,
        endpoint_id: int | None = None,
        suffix: str = "light",
    ) -> None:
        super().__init__(coordinator, device)
        self._endpoint_id = endpoint_id
        self._attr_unique_id = f"{DOMAIN}-{device.node_id}-{suffix}"
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
        if (
            self._endpoint_id is not None
            and self._uses_endpoint_power(self._endpoint_id)
            and self._simple_light_turn_on(kwargs)
        ):
            await self._switch_endpoint_power(self._endpoint_id, "ON")
            return

        await self._mixed_endpoint_workaround()
        changes = self._build_turn_on_changes(kwargs, restore_last_brightness=True)
        if changes.get("power") == "OFF":
            await self.async_turn_off(**kwargs)
            return
        await self.coordinator.api.async_change_light_state(
            self._device.home_id,
            self._device.node_id,
            changes,
        )
        self._cache_global_light_on(self.coordinator)
        self._update_light_endpoint_cache("ON", self._endpoint_id)
        if "brightness" in changes:
            self.coordinator.update_cached_value(self.node_id, "brightness", changes["brightness"])
        if "colorTemperature" in changes:
            self.coordinator.update_cached_value(
                self.node_id,
                "colorTemperature",
                changes["colorTemperature"],
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self._endpoint_id is not None and self._uses_endpoint_power(self._endpoint_id):
            await self._switch_endpoint_power(self._endpoint_id, "OFF")
            return

        await self.coordinator.api.async_change_light_state(
            self._device.home_id,
            self._device.node_id,
            {"power": "OFF"},
        )
        self._cache_global_light_off(self.coordinator)
        self._update_light_endpoint_cache("OFF", self._endpoint_id)


class EnkiLightEntity(EnkiLightBehaviorMixin, EnkiEntity, LightEntity, RestoreEntity):
    """Standard Enki light or dimmer node."""

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

        if profile.is_gdansk_ble:
            modes.update({ColorMode.COLOR_TEMP, ColorMode.HS, ColorMode.BRIGHTNESS})
            self._color_temp_values = self._parse_color_temp_values(possible)
            if self._color_temp_values:
                self._attr_min_color_temp_kelvin = min(self._color_temp_values)
                self._attr_max_color_temp_kelvin = max(self._color_temp_values)
            else:
                self._attr_min_color_temp_kelvin = 2700
                self._attr_max_color_temp_kelvin = 6500
            self._brightness_max = 100
        elif "change_color_temperature" in caps:
            modes.add(ColorMode.COLOR_TEMP)
            self._color_temp_values = self._parse_color_temp_values(possible)
            if self._color_temp_values:
                self._attr_min_color_temp_kelvin = min(self._color_temp_values)
                self._attr_max_color_temp_kelvin = max(self._color_temp_values)
            else:
                self._attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
                self._attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

        if "change_hue" in caps and "change_saturation" in caps:
            modes.add(ColorMode.HS)

        if "change_brightness" in caps:
            modes.add(ColorMode.BRIGHTNESS)
            if not profile.is_gdansk_ble:
                self._brightness_max = self._parse_brightness_max(possible)

        if not modes and profile.supports_electrical_power:
            modes.add(ColorMode.ONOFF)

        supported = {
            ColorMode(value)
            for value in select_light_color_modes(
                has_hs=ColorMode.HS in modes,
                has_color_temp=ColorMode.COLOR_TEMP in modes,
                has_brightness=ColorMode.BRIGHTNESS in modes,
            )
        }
        self._attr_supported_color_modes = supported or {ColorMode.ONOFF}
        if len(self._attr_supported_color_modes) == 1:
            self._attr_color_mode = next(iter(self._attr_supported_color_modes))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self._device.profile.is_gdansk_ble:
            return
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        restored = self._restore_gdansk_state_from_last_state(
            last_state.state,
            last_state.attributes,
        )
        if restored:
            self.coordinator.update_cached_values(self._device.node_id, restored)

    @property
    def is_on(self) -> bool:
        reported = self._device.reported
        if self._endpoint_id is not None:
            power = reported.endpoint_power(self._endpoint_id)
            return power == "ON" if power is not None else False

        if self._supports_light_state:
            if reported.global_power is not None:
                return reported.global_power == "ON"
            return False

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

    @property
    def hs_color(self) -> tuple[float, float] | None:
        if (
            self._attr_supported_color_modes is None
            or ColorMode.HS not in self._attr_supported_color_modes
        ):
            return None
        reported = self._device.reported
        return enki_to_hs(reported.hue, reported.saturation)

    @property
    def color_mode(self) -> ColorMode | None:
        if self._attr_color_mode is not None:
            return self._attr_color_mode
        reported = self._device.reported
        mode = reported.color_mode
        if mode == "hs":
            return ColorMode.HS
        if mode == "ct":
            return ColorMode.COLOR_TEMP
        if reported.color_temperature:
            return ColorMode.COLOR_TEMP
        if ColorMode.HS in (self._attr_supported_color_modes or set()):
            return ColorMode.HS
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id

        if self._device.profile.is_gdansk_ble:
            hs_color = kwargs.get(ATTR_HS_COLOR)
            wants_state_change = bool(kwargs)
            power = True if (not self.is_on or not wants_state_change) else None
            state = await self.coordinator.api.async_apply_gdansk_light_state(
                self._device,
                power=power,
                brightness=kwargs.get("brightness"),
                color_temp_kelvin=kwargs.get("color_temp_kelvin"),
                hs_color=hs_color,
            )
            self.coordinator.update_cached_values(node_id, state)
            self._update_light_endpoint_cache("ON", self._endpoint_id)
            await self._async_log_gdansk_activity(kwargs, power=True)
            return

        if not self._supports_light_state:
            await self.coordinator.api.async_switch_electrical_power(
                home_id,
                node_id,
                "ON",
                endpoint=self._endpoint_id,
            )
            self._cache_electrical_power("ON")
            return

        if (
            self._endpoint_id is not None
            and self._uses_endpoint_power(self._endpoint_id)
            and self._simple_light_turn_on(kwargs)
            and ATTR_HS_COLOR not in kwargs
        ):
            await self._switch_endpoint_power(self._endpoint_id, "ON")
            return

        if ATTR_HS_COLOR in kwargs:
            hue, saturation = hs_to_enki(*kwargs[ATTR_HS_COLOR])
            await self.coordinator.api.async_change_light_color(home_id, node_id, hue, saturation)
            self.coordinator.update_cached_value(node_id, "hue", hue)
            self.coordinator.update_cached_value(node_id, "saturation", saturation)
            self.coordinator.update_cached_value(node_id, "colorMode", "hs")
            self.coordinator.update_cached_value(node_id, "colorTemperature", None)
            self.coordinator.update_cached_value(node_id, "power", "ON")
            self._update_light_endpoint_cache("ON", self._endpoint_id)
            return

        await self._mixed_endpoint_workaround()
        changes = self._build_turn_on_changes(kwargs)
        if changes.get("power") == "OFF":
            await self.async_turn_off(**kwargs)
            return
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
            self.coordinator.update_cached_value(node_id, "colorMode", "ct")
        self._update_light_endpoint_cache("ON", self._endpoint_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        home_id = self._device.home_id
        node_id = self._device.node_id

        if self._device.profile.is_gdansk_ble:
            state = await self.coordinator.api.async_apply_gdansk_light_state(
                self._device,
                power=False,
            )
            self.coordinator.update_cached_values(node_id, state)
            self._update_light_endpoint_cache("OFF", self._endpoint_id)
            await self._async_log_gdansk_activity({}, power=False)
            return

        if not self._supports_light_state:
            await self.coordinator.api.async_switch_electrical_power(
                home_id,
                node_id,
                "OFF",
                endpoint=self._endpoint_id,
            )
            self._cache_electrical_power("OFF")
            return

        if self._endpoint_id is not None and self._uses_endpoint_power(self._endpoint_id):
            await self._switch_endpoint_power(self._endpoint_id, "OFF")
            return

        await self.coordinator.api.async_change_light_state(
            home_id,
            node_id,
            {"power": "OFF"},
        )
        self.coordinator.update_cached_value(node_id, "power", "OFF")
        self._update_light_endpoint_cache("OFF", self._endpoint_id)

    def _cache_electrical_power(self, power: str) -> None:
        node_id = self._device.node_id
        if self._endpoint_id is not None:
            self.coordinator.update_endpoint_power(node_id, self._endpoint_id, power)
            return
        self.coordinator.update_cached_value(node_id, "electrical_power", power)
        self.coordinator.update_cached_value(node_id, "power", power)

    async def _async_log_gdansk_activity(
        self,
        kwargs: dict[str, Any],
        *,
        power: bool,
    ) -> None:
        hass = getattr(self, "hass", None)
        if hass is None:
            return
        if not power:
            message = "Turned off via local BLE"
        elif ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            message = f"Set color to {round(hue)}°, {round(sat)}%"
        elif "color_temp_kelvin" in kwargs:
            message = f"Set color temperature to {kwargs['color_temp_kelvin']}K"
        elif "brightness" in kwargs:
            percent = round(int(kwargs["brightness"]) * 100 / 255)
            message = f"Set brightness to {percent}%"
        else:
            message = "Turned on via local BLE"
        await hass.services.async_call(
            "logbook",
            "log",
            {
                "name": self.name or self.entity_id,
                "message": message,
                "entity_id": self.entity_id,
            },
            blocking=False,
            context=self._context,
        )

    def _restore_gdansk_state_from_last_state(
        self,
        state: str,
        attributes: dict[str, Any],
    ) -> dict[str, Any]:
        restored: dict[str, Any] = {
            "power": "ON" if state == STATE_ON else "OFF",
            "light_power": "ON" if state == STATE_ON else "OFF",
        }
        brightness = attributes.get("brightness")
        if isinstance(brightness, (int, float)):
            restored["brightness"] = round(max(0, min(255, float(brightness))) * 100 / 255)
        color_temp_kelvin = attributes.get("color_temp_kelvin")
        if isinstance(color_temp_kelvin, (int, float)):
            restored["colorTemperature"] = f"T{round(color_temp_kelvin)}K"
            restored["colorMode"] = "ct"
        hs_color = attributes.get("hs_color")
        if (
            isinstance(hs_color, (list, tuple))
            and len(hs_color) == 2
            and all(isinstance(value, (int, float)) for value in hs_color)
        ):
            hue, saturation = hs_to_enki(float(hs_color[0]), float(hs_color[1]))
            restored["hue"] = hue
            restored["saturation"] = saturation
            restored["colorMode"] = "hs"
        color_mode = attributes.get("color_mode")
        if isinstance(color_mode, str) and color_mode in {"hs", "color_temp"}:
            restored["colorMode"] = "hs" if color_mode == "hs" else "ct"
        return restored
