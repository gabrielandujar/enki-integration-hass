"""Unit tests for the GDANSK BLE protocol helpers."""

from __future__ import annotations

from enki.api.ble_gdansk import (
    GdanskBleState,
    build_brightness_frame,
    build_color_temp_frame,
    build_frame,
    build_handshake_frame,
    build_hs_frame,
    build_power_frame,
    extract_ble_address,
    gdansk_state_to_enki_payload,
    parse_notification,
)


def test_build_handshake_frame() -> None:
    assert build_handshake_frame() == bytes.fromhex("00002001020002")


def test_build_power_frame() -> None:
    assert build_power_frame(True) == bytes.fromhex("0000100103010000")
    assert build_power_frame(False) == bytes.fromhex("0000100103000000")


def test_build_brightness_frame() -> None:
    assert build_brightness_frame(50) == bytes.fromhex("0000110103800000")


def test_build_color_temp_frame() -> None:
    assert build_color_temp_frame(4000) == bytes.fromhex("000012010400fa0000")


def test_build_hs_frame() -> None:
    assert build_hs_frame(180, 50) == bytes.fromhex("000013070480800000")


def test_parse_notifications_update_state() -> None:
    state = GdanskBleState()

    assert parse_notification(build_frame(0x1003, bytes((1,))), state) == 0x1003
    assert state.power is True

    assert parse_notification(build_frame(0x1103, bytes((0x80,))), state) == 0x1103
    assert state.brightness_pct == 50

    assert parse_notification(build_frame(0x1203, bytes.fromhex("00fa")), state) == 0x1203
    assert state.color_temp_kelvin == 4000
    assert state.color_mode == "ct"

    assert parse_notification(build_frame(0x130E, bytes((1,))), state) == 0x130E
    assert state.raw_mode == 1
    assert state.color_mode == "hs"

    assert parse_notification(build_frame(0x1309, bytes((0x80, 0x80))), state) == 0x1309
    assert state.hue == 180.71
    assert state.saturation == 50.2
    assert state.color_mode == "hs"


def test_gdansk_state_maps_to_enki_payload() -> None:
    payload = gdansk_state_to_enki_payload(
        GdanskBleState(
            power=True,
            brightness_pct=42,
            color_temp_kelvin=3200,
            hue=210,
            saturation=80,
            color_mode="hs",
            raw_mode=1,
        )
    )
    assert payload == {
        "power": "ON",
        "light_power": "ON",
        "brightness": 42.0,
        "colorTemperature": "T3200K",
        "hue": 0.58,
        "saturation": 0.8,
        "colorMode": "hs",
        "gdansk_raw_mode": 1,
    }


def test_extract_ble_address_prefers_explicit_mac() -> None:
    assert extract_ble_address({"macAddress": "f0:82:c0:49:d7:d2"}) == "F0:82:C0:49:D7:D2"


def test_extract_ble_address_falls_back_to_eui64() -> None:
    assert extract_ble_address({"eui64": "f082c049d7d2"}) == "F0:82:C0:49:D7:D2"
