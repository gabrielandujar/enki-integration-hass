"""Capability-based Enki device detection (referentiel + BFF metadata)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import DEVICE_TYPE_FANS, DEVICE_TYPE_INVERTERS, DEVICE_TYPE_LIGHTS
from .models import EnkiDevice


def capabilities_set(capabilities: list[str] | dict[str, Any] | None) -> set[str]:
    """Normalize referentiel capabilities to a string set."""
    if isinstance(capabilities, list):
        return {capability for capability in capabilities if isinstance(capability, str)}
    if isinstance(capabilities, dict):
        return set(capabilities.keys())
    return set()


def possible_values_dict(possible_values: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(possible_values, dict):
        return possible_values
    return {}


def _supports(capabilities: set[str], possible_values: dict[str, Any], *names: str) -> bool:
    """True when any capability name appears in capabilities or possibleValues."""
    return any(name in capabilities or name in possible_values for name in names)


@dataclass(frozen=True, slots=True)
class EnkiCapabilityProfile:
    """Read-only view of what a physical Enki node can do.

    Built from referentiel metadata (authoritative for commands) and optional
    BFF dashboard fields (used for multi-endpoint outlets and solar tiles).
    """

    device_type: str
    capabilities: frozenset[str]
    possible_values: dict[str, Any]
    bff_device_type: str = ""
    main_change_capability_id: str | None = None
    main_change_capability_endpoints: tuple[int, ...] = ()
    power_production: float | None = None

    @classmethod
    def from_device(cls, device: EnkiDevice) -> EnkiCapabilityProfile:
        """Build a profile snapshot from a discovered device."""
        endpoints: list[int] = []
        for endpoint in device.main_change_capability_endpoints:
            if isinstance(endpoint, int):
                endpoints.append(endpoint)
            elif isinstance(endpoint, dict):
                endpoint_id = endpoint.get("id")
                if isinstance(endpoint_id, int):
                    endpoints.append(endpoint_id)
        return cls(
            device_type=device.device_type,
            capabilities=frozenset(capabilities_set(device.capabilities)),
            possible_values=possible_values_dict(device.possible_values),
            bff_device_type=device.bff_device_type,
            main_change_capability_id=device.main_change_capability_id,
            main_change_capability_endpoints=tuple(sorted(set(endpoints))),
            power_production=device.power_production,
        )

    # --- capability probes -------------------------------------------------

    @property
    def supports_light_state(self) -> bool:
        return _supports(
            self.capabilities,
            self.possible_values,
            "change_light_state",
            "check_light_state",
        )

    @property
    def supports_electrical_power(self) -> bool:
        return _supports(
            self.capabilities,
            self.possible_values,
            "switch_electrical_power",
            "check_electrical_power",
        )

    @property
    def supports_fan_speed(self) -> bool:
        return _supports(
            self.capabilities,
            self.possible_values,
            "change_fan_speed",
            "check_fan_speed",
        )

    @property
    def supports_fan_rotation(self) -> bool:
        return _supports(
            self.capabilities,
            self.possible_values,
            "change_fan_rotation_direction",
            "check_fan_rotation_direction",
        )

    @property
    def supports_airflow_mode(self) -> bool:
        return _supports(
            self.capabilities,
            self.possible_values,
            "change_airflow_mode",
            "check_airflow_mode",
        )

    @property
    def supports_power_production(self) -> bool:
        return "check_power_production" in self.capabilities

    # --- HA platform classification ----------------------------------------

    @property
    def is_fan(self) -> bool:
        """Ceiling fans and VMC nodes (airflow-prod API)."""
        if self.device_type == DEVICE_TYPE_FANS:
            return True
        return self.supports_fan_speed or self.supports_fan_rotation or self.supports_airflow_mode

    @property
    def is_light_controllable(self) -> bool:
        """Lights, dimmers, fan kits, and power-only outlets."""
        if self.device_type == DEVICE_TYPE_LIGHTS:
            return True
        if self.is_fan:
            return self.supports_light_state
        return self.supports_light_state or self.supports_electrical_power

    @property
    def is_inverter(self) -> bool:
        """Solar inverters with live production on the BFF dashboard."""
        if self.device_type in {DEVICE_TYPE_INVERTERS, "inverters"}:
            return self.power_production is not None
        return self.supports_power_production and self.power_production is not None

    @property
    def is_supported(self) -> bool:
        return self.is_fan or self.is_light_controllable or self.is_inverter

    @property
    def uses_power_api_only(self) -> bool:
        """Pure switches/outlets (e.g. Edisio) without the lighting API."""
        return self.supports_electrical_power and not self.supports_light_state

    @property
    def fan_max_speed(self) -> int | None:
        """Max non-off speed step from referentiel possibleValues."""
        speed_meta = self.possible_values.get("change_fan_speed") or self.possible_values.get(
            "check_fan_speed"
        )
        if isinstance(speed_meta, dict):
            speed_range = speed_meta.get("range")
            if isinstance(speed_range, dict):
                raw_max = speed_range.get("max")
                if isinstance(raw_max, (int, float)) and raw_max > 0:
                    return max(1, int(round(raw_max)))
        return None

    @property
    def power_switch_endpoints(self) -> list[int]:
        """BFF endpoints when mainChangeCapability is switch_electrical_power."""
        if self.main_change_capability_id != "switch_electrical_power":
            return []
        return list(self.main_change_capability_endpoints)


def parse_bff_power(description: dict[str, Any] | None) -> float | None:
    """Parse power production from BFF description.value (e.g. '109 W' -> 109.0)."""
    if not description or not isinstance(description, dict):
        return None
    value_str = description.get("value")
    if not isinstance(value_str, str):
        return None
    try:
        return float(value_str.split()[0])
    except (ValueError, IndexError):
        return None


# --- Backward-compatible module functions (used by tests and legacy imports) ---


def supports_light_state(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return _supports(capabilities, possible_values, "change_light_state", "check_light_state")


def supports_electrical_power(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return _supports(
        capabilities,
        possible_values,
        "switch_electrical_power",
        "check_electrical_power",
    )


def supports_fan_speed(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return _supports(capabilities, possible_values, "change_fan_speed", "check_fan_speed")


def supports_fan_rotation(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return _supports(
        capabilities,
        possible_values,
        "change_fan_rotation_direction",
        "check_fan_rotation_direction",
    )


def supports_airflow_mode(capabilities: set[str], possible_values: dict[str, Any]) -> bool:
    return _supports(
        capabilities,
        possible_values,
        "change_airflow_mode",
        "check_airflow_mode",
    )


def supports_power_production(capabilities: set[str]) -> bool:
    return "check_power_production" in capabilities


def device_capabilities(device: EnkiDevice) -> set[str]:
    return set(device.profile.capabilities)


def device_possible_values(device: EnkiDevice) -> dict[str, Any]:
    return device.profile.possible_values


def is_fan_device(device: EnkiDevice) -> bool:
    return device.profile.is_fan


def is_light_controllable(device: EnkiDevice) -> bool:
    return device.profile.is_light_controllable


def is_inverter_device(device: EnkiDevice) -> bool:
    return device.profile.is_inverter


def device_is_supported(device: EnkiDevice) -> bool:
    return device.profile.is_supported


def device_uses_power_api_only(device: EnkiDevice) -> bool:
    return device.profile.uses_power_api_only


def fan_max_speed(device: EnkiDevice) -> int | None:
    return device.profile.fan_max_speed


def main_change_capability_endpoints(device: EnkiDevice) -> list[int]:
    return device.profile.power_switch_endpoints
