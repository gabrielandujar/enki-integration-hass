"""Enki domain model (no Home Assistant imports)."""

from .capabilities import (
    EnkiCapabilityProfile,
    capabilities_set,
    device_is_supported,
    device_uses_power_api_only,
    fan_max_speed,
    is_fan_device,
    is_inverter_device,
    is_light_controllable,
    main_change_capability_endpoints,
    possible_values_dict,
    supports_airflow_mode,
    supports_electrical_power,
    supports_fan_rotation,
    supports_fan_speed,
    supports_light_state,
    supports_power_production,
)
from .models import EnkiDevice, EnkiDiscoveryRecord
from .profile import (
    build_discovery_record,
    build_github_new_issue_url,
    integration_supports_device,
    profile_fingerprint,
    profile_to_export_dict,
)
from .state import EnkiDeviceState

__all__ = [
    "EnkiCapabilityProfile",
    "EnkiDevice",
    "EnkiDeviceState",
    "EnkiDiscoveryRecord",
    "build_discovery_record",
    "build_github_new_issue_url",
    "capabilities_set",
    "device_is_supported",
    "device_uses_power_api_only",
    "fan_max_speed",
    "integration_supports_device",
    "is_fan_device",
    "is_inverter_device",
    "is_light_controllable",
    "main_change_capability_endpoints",
    "possible_values_dict",
    "profile_fingerprint",
    "profile_to_export_dict",
    "supports_airflow_mode",
    "supports_electrical_power",
    "supports_fan_rotation",
    "supports_fan_speed",
    "supports_light_state",
    "supports_power_production",
]
