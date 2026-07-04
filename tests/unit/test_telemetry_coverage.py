"""Unit tests for telemetry coverage decisions."""

from __future__ import annotations

from enki.domain.profile import build_discovery_record
from enki.domain.telemetry_coverage import (
    capability_is_covered,
    discovery_record_needs_telemetry,
    profile_from_record,
)

# Capabilities from issue #14 — Inspire AD_TCFL_1 ceiling fan (already fully supported).
_CEILING_FAN_CAPABILITIES = [
    "change_airflow_mode",
    "change_brightness",
    "change_color_temperature",
    "change_esdk_certificate",
    "change_fan_rotation_direction",
    "change_fan_speed",
    "change_light_state",
    "check_airflow_mode",
    "check_certificate_renewal_confirmation",
    "check_current_firmware_version",
    "check_electrical_power",
    "check_esdk_certificate_renewal",
    "check_fan_rotation_direction",
    "check_fan_speed",
    "check_light_state",
    "execute_generic_ota_command",
    "ota_inventory",
    "switch_electrical_power",
]


def _ceiling_fan_record(*, supported: bool = True):
    return build_discovery_record(
        device_type="ceiling_fans",
        bff_device_type="ceiling_fans",
        capabilities=_CEILING_FAN_CAPABILITIES,
        possible_values={
            "change_airflow_mode": {"values": ["BREEZE", "MANUAL"]},
            "change_color_temperature": {"values": ["T3500K", "T4000K"]},
            "change_fan_rotation_direction": {"values": ["CLOCKWISE", "COUNTERCLOCKWISE"]},
        },
        manufacturer="Inspire",
        model="AD_TCFL_1",
        firmware_version="2.21.0",
        supported_by_integration=supported,
    )


def test_ceiling_fan_profile_does_not_need_telemetry() -> None:
    record = _ceiling_fan_record()
    assert discovery_record_needs_telemetry(record) is False


def test_unsupported_device_still_needs_telemetry() -> None:
    record = build_discovery_record(
        device_type="equation_radiator",
        bff_device_type="radiators",
        capabilities=["check_temperature"],
        possible_values={},
        manufacturer="equation",
        model="neo",
        firmware_version=None,
        supported_by_integration=False,
    )
    assert discovery_record_needs_telemetry(record) is True


def test_supported_device_with_unknown_capability_needs_telemetry() -> None:
    record = build_discovery_record(
        device_type="ceiling_fans",
        bff_device_type="ceiling_fans",
        capabilities=["change_fan_speed", "check_fan_speed", "change_setpoint"],
        possible_values={},
        manufacturer="Inspire",
        model="future_fan",
        firmware_version="1.0.0",
        supported_by_integration=True,
    )
    assert discovery_record_needs_telemetry(record) is True


def test_admin_capabilities_are_ignored() -> None:
    profile = profile_from_record(_ceiling_fan_record())
    assert capability_is_covered("ota_inventory", profile) is True
    assert capability_is_covered("change_esdk_certificate", profile) is True


def test_sonoff_profile_not_eligible_for_telemetry() -> None:
    record = build_discovery_record(
        device_type="sensors",
        bff_device_type="sensors",
        capabilities=["check_current_temperature"],
        possible_values={},
        manufacturer="Sonoff",
        model="SNZB-02D",
        firmware_version="1.0.0",
        supported_by_integration=False,
    )
    assert discovery_record_needs_telemetry(record) is False


def test_gateway_profile_not_eligible_for_telemetry() -> None:
    record = build_discovery_record(
        device_type="gateways",
        bff_device_type="gateways",
        capabilities=["gateway_reboot", "gateway_inventory", "check_gateway_state"],
        possible_values={},
        manufacturer="Enki",
        model="EnkiConnectGW001",
        firmware_version="2.0.0",
        supported_by_integration=False,
    )
    assert discovery_record_needs_telemetry(record) is False
