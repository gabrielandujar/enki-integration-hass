"""Unit tests for shutter position helpers."""

from __future__ import annotations

from unittest.mock import patch

from enki.domain.capabilities import is_cover_device
from enki.domain.models import EnkiDevice
from enki.domain.state import EnkiDeviceState
from enki.lib.shutter import normalize_shutter_position, shutter_opening_is_closed

_COVER_DEVICE_KWARGS = {
    "home_id": "h",
    "device_id": "d",
    "node_id": "n",
    "device_name": "VR Salon",
    "device_type": "access_and_motorizations",
    "is_enabled": True,
    "state": "ACTIVE",
    "capabilities": ["change_shutter_position", "check_shutter_position"],
}


def test_normalize_shutter_position() -> None:
    assert normalize_shutter_position(0) == 0
    assert normalize_shutter_position(50.4) == 50
    assert normalize_shutter_position(100) == 100
    assert normalize_shutter_position("bad") is None


def test_shutter_opening_is_closed() -> None:
    assert shutter_opening_is_closed("CLOSED") is True
    assert shutter_opening_is_closed("open") is False


def test_is_cover_device_from_capabilities() -> None:
    with patch("enki.domain.capabilities.ENKI_ACCESS_MOTORIZATION_API_KEY", "test-key"):
        device = EnkiDevice(**_COVER_DEVICE_KWARGS)
        assert is_cover_device(device) is True


def test_is_cover_device_requires_motorization_key() -> None:
    with patch("enki.domain.capabilities.ENKI_ACCESS_MOTORIZATION_API_KEY", ""):
        device = EnkiDevice(**_COVER_DEVICE_KWARGS)
        assert is_cover_device(device) is False


def test_device_state_shutter_fields() -> None:
    state = EnkiDeviceState(
        {
            "shutter_position": 42,
            "shutter_opening": "OPEN",
        }
    )
    assert state.shutter_position == 42
    assert state.shutter_opening == "OPEN"
