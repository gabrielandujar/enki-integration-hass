"""Capability → micro-service routing for state reads."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..domain.capabilities import EnkiCapabilityProfile


@dataclass(frozen=True, slots=True)
class CapabilityRead:
    """Maps a referentiel check_* capability to a transport read."""

    transport_id: str
    capability: str
    state_key: str
    skip: Callable[[EnkiCapabilityProfile], bool] | None = None


def _skip_thermostat_temperature(profile: EnkiCapabilityProfile) -> bool:
    return profile.supports_thermostat


def _skip_non_thermostat_temperature(profile: EnkiCapabilityProfile) -> bool:
    return not profile.supports_thermostat


CAPABILITY_READS: tuple[CapabilityRead, ...] = (
    CapabilityRead(
        "temperature_humidity",
        "check_current_temperature",
        "current_temperature",
        skip=_skip_thermostat_temperature,
    ),
    CapabilityRead("temperature_humidity", "check_current_humidity", "current_humidity"),
    CapabilityRead("battery_health", "check_battery_health", "battery_health"),
    CapabilityRead("luminosity_sensor", "check_illuminance_level", "illuminance_level"),
    CapabilityRead("presence_detector", "check_motion_detection", "motion_detection"),
    CapabilityRead("presence_detector", "check_motion_detector_state", "motion_detector_state"),
    CapabilityRead("contact_sensor", "check_contact_sensor_state", "contact_sensor_state"),
    CapabilityRead("contact_sensor", "check_vibration_detection", "vibration_detection"),
    CapabilityRead(
        "contact_sensor",
        "check_vibration_detection_activation",
        "vibration_detection_activation",
    ),
    CapabilityRead(
        "contact_sensor",
        "check_contact_detection_activation",
        "contact_detection_activation",
    ),
    CapabilityRead(
        "contact_sensor",
        "check_vibration_sensibility_level",
        "vibration_sensibility_level",
    ),
    CapabilityRead("siren", "check_siren_global_state", "siren_global_state"),
    CapabilityRead("water_sensor", "check_water_sensor_state", "water_sensor_state"),
    CapabilityRead("heating", "check_pilot_wire_state", "pilot_wire_state"),
    CapabilityRead(
        "heating",
        "check_thermostat_target_temperature",
        "thermostat_target_temperature",
    ),
    CapabilityRead("heating", "check_thermostat_running_state", "thermostat_running_state"),
    CapabilityRead(
        "heating",
        "check_current_temperature",
        "current_temperature",
        skip=_skip_non_thermostat_temperature,
    ),
    CapabilityRead("heating", "check_window_open_detection", "window_open_detection"),
    CapabilityRead("heating", "check_window_open_detection_mode", "window_open_detection_mode"),
    CapabilityRead("heating", "check_occupancy", "occupancy"),
    CapabilityRead("heating", "check_occupancy_mode", "occupancy_mode"),
)
