"""Unit tests for fan rotation capability detection."""

from __future__ import annotations

from enki.fan_rotation_helpers import device_supports_fan_rotation
from enki.models import EnkiDevice


def test_device_supports_fan_rotation_from_capabilities() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
        capabilities=["change_fan_rotation_direction"],
    )
    assert device_supports_fan_rotation(device) is True


def test_device_supports_fan_rotation_from_possible_values() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
        possible_values={"check_fan_rotation_direction": {"values": ["CLOCKWISE"]}},
    )
    assert device_supports_fan_rotation(device) is True


def test_device_without_rotation_capability() -> None:
    device = EnkiDevice(
        home_id="h",
        device_id="d",
        node_id="n",
        device_name="Fan",
        device_type="ceiling_fans",
        is_enabled=True,
        state="ACTIVE",
    )
    assert device_supports_fan_rotation(device) is False
