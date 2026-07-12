"""Local BLE control for the GDANSK / ZBEK-29 ceiling panel."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..const import LOGGER
from ..exceptions import EnkiConnectionError

if TYPE_CHECKING:
    from collections.abc import Callable

GDANSK_REFERENTIEL_MODEL = "ZBEK-29"
GDANSK_MODEL_NUMBERS = {
    GDANSK_REFERENTIEL_MODEL,
    "60AFAB582985C158F8A946D0",
}
GDANSK_SERVICE_UUID = "0000a100-1115-1000-0001-617573746f6d"
GDANSK_WRITE_UUID = "0000a101-1115-1000-0001-617573746f6d"
GDANSK_NOTIFY_UUID = "0000a102-1115-1000-0001-617573746f6d"

_HANDSHAKE_DELAY = 0.2
_COMMAND_TIMEOUT = 4.0
_QUERY_SETTLE_DELAY = 0.2
_MAC_RE = re.compile(r"^[0-9A-F]{12}$")


def be16(value: int) -> bytes:
    """Encode a 16-bit unsigned integer in big-endian order."""
    return bytes(((value >> 8) & 0xFF, value & 0xFF))


def build_frame(opcode: int, payload: bytes = b"") -> bytes:
    """Build one GDANSK BLE frame."""
    return b"\x00\x00" + be16(opcode) + (bytes((len(payload),)) + payload if payload else b"")


def build_handshake_frame() -> bytes:
    return build_frame(0x2001, be16(2))


def build_power_frame(power_on: bool) -> bytes:
    return build_frame(0x1001, bytes((1 if power_on else 0, 0, 0)))


def build_brightness_frame(brightness_pct: int) -> bytes:
    level = max(0, min(100, brightness_pct))
    raw = round(level * 255 / 100)
    return build_frame(0x1101, bytes((raw, 0, 0)))


def build_color_temp_frame(kelvin: int) -> bytes:
    mirek = round(1_000_000 / max(kelvin, 1))
    return build_frame(0x1201, be16(mirek) + b"\x00\x00")


def build_hs_frame(hue: float, saturation: float) -> bytes:
    hue = max(0.0, min(360.0, hue))
    saturation = max(0.0, min(100.0, saturation))
    raw_hue = round(hue / 360 * 255)
    raw_sat = min(round(saturation / 100 * 255), 254)
    return build_frame(0x1307, bytes((raw_hue, raw_sat, 0, 0)))


def query_frames() -> tuple[tuple[int, bytes], ...]:
    """Return BLE query frames paired with their expected notification opcode."""
    return (
        (0x1003, build_frame(0x1002)),
        (0x1103, build_frame(0x1102)),
        (0x130E, build_frame(0x130D)),
        (0x1203, build_frame(0x1202)),
    )


@dataclass(slots=True)
class GdanskBleState:
    """Mutable GDANSK state mirrored from BLE notifications."""

    power: bool | None = None
    brightness_pct: int | None = None
    color_temp_kelvin: int | None = None
    hue: float | None = None
    saturation: float | None = None
    color_mode: str | None = None
    raw_mode: int | None = None


def parse_notification(data: bytes, state: GdanskBleState) -> int | None:
    """Apply one BLE notification to the cached GDANSK state."""
    if len(data) < 5:
        return None
    opcode = int.from_bytes(data[2:4], "big")
    payload = data[5:]
    if opcode == 0x1003 and payload:
        state.power = payload[0] != 0
    elif opcode == 0x1103 and payload:
        state.brightness_pct = round(payload[0] * 100 / 255)
    elif opcode == 0x1203 and len(payload) >= 2:
        mirek = int.from_bytes(payload[:2], "big")
        state.color_temp_kelvin = round(1_000_000 / max(mirek, 1))
        state.color_mode = "ct"
    elif opcode == 0x130E and payload:
        state.raw_mode = payload[0]
        if payload[0] in {0, 2}:
            state.color_mode = "ct"
        else:
            state.color_mode = "hs"
    elif opcode == 0x1309 and len(payload) >= 2:
        state.hue = round(payload[0] * 360 / 255, 2)
        state.saturation = round(payload[1] / 255 * 100, 2)
        state.color_mode = "hs"
    return opcode


def gdansk_state_to_enki_payload(state: GdanskBleState) -> dict[str, Any]:
    """Translate BLE cache fields to the cloud-style keys used by entities."""
    payload: dict[str, Any] = {}
    if state.power is not None:
        payload["power"] = "ON" if state.power else "OFF"
        payload["light_power"] = payload["power"]
    if state.brightness_pct is not None:
        payload["brightness"] = float(state.brightness_pct)
    if state.color_temp_kelvin is not None:
        payload["colorTemperature"] = f"T{state.color_temp_kelvin}K"
    if state.hue is not None:
        payload["hue"] = round(state.hue / 360, 2)
    if state.saturation is not None:
        payload["saturation"] = round(state.saturation / 100, 2)
    if state.color_mode is not None:
        payload["colorMode"] = state.color_mode
    if state.raw_mode is not None:
        payload["gdansk_raw_mode"] = state.raw_mode
    return payload


def extract_ble_address(metadata: dict[str, Any]) -> str | None:
    """Resolve the panel BLE MAC from discovery metadata."""
    for key in (
        "bluetooth_address",
        "bluetoothAddress",
        "bluetooth_mac_address",
        "bluetoothMacAddress",
        "mac_address",
        "macAddress",
        "address",
    ):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()

    raw_eui64 = metadata.get("eui64")
    if isinstance(raw_eui64, str):
        normalized = raw_eui64.replace(":", "").replace("-", "").strip().upper()
        if _MAC_RE.fullmatch(normalized):
            return ":".join(normalized[index : index + 2] for index in range(0, 12, 2))
    return None


class GdanskBleBackend:
    """Single-device BLE session manager for GDANSK."""

    def __init__(
        self,
        address: str,
        *,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._address = address
        self._client_factory = client_factory
        self._state = GdanskBleState()
        self._lock = asyncio.Lock()
        self._pending: dict[int, list[asyncio.Future[bytes]]] = {}

    async def async_fetch_state(self) -> dict[str, Any]:
        """Read the current GDANSK state via local BLE."""
        async with self._lock:
            return await self._with_client(self._async_query_state)

    async def async_apply(
        self,
        *,
        power: bool | None = None,
        brightness_pct: int | None = None,
        color_temp_kelvin: int | None = None,
        hs_color: tuple[float, float] | None = None,
    ) -> dict[str, Any]:
        """Apply one or more changes and return the refreshed state."""
        async with self._lock:
            return await self._with_client(
                self._async_apply_changes,
                power=power,
                brightness_pct=brightness_pct,
                color_temp_kelvin=color_temp_kelvin,
                hs_color=hs_color,
            )

    async def _with_client(self, operation: Any, **kwargs: Any) -> dict[str, Any]:
        client = self._make_client()
        try:
            async with client:
                LOGGER.debug("GDANSK BLE connected to %s", self._address)
                await client.start_notify(GDANSK_NOTIFY_UUID, self._handle_notification)
                try:
                    await self._async_handshake(client)
                    return await operation(client, **kwargs)
                finally:
                    await client.stop_notify(GDANSK_NOTIFY_UUID)
        except Exception as err:  # noqa: BLE001
            LOGGER.debug(
                "GDANSK BLE failure for %s: %s",
                self._address,
                err,
                exc_info=LOGGER.isEnabledFor(logging.DEBUG),
            )
            raise EnkiConnectionError(
                f"GDANSK BLE control failed for {self._address}: {err}",
                service="bluetooth",
            ) from err

    def _make_client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory(self._address, timeout=20.0)
        try:
            from bleak import BleakClient
        except ImportError as err:  # pragma: no cover - depends on runtime packaging
            raise EnkiConnectionError(
                "Bleak is not installed; GDANSK BLE control is unavailable",
                service="bluetooth",
            ) from err
        return BleakClient(self._address, timeout=20.0)

    async def _async_handshake(self, client: Any) -> None:
        LOGGER.debug("GDANSK BLE handshake %s", build_handshake_frame().hex())
        await client.write_gatt_char(
            GDANSK_WRITE_UUID,
            build_handshake_frame(),
            response=True,
        )
        await asyncio.sleep(_HANDSHAKE_DELAY)

    async def _async_query_state(self, client: Any) -> dict[str, Any]:
        for expected_opcode, frame in query_frames():
            LOGGER.debug("GDANSK BLE query opcode=0x%04x frame=%s", expected_opcode, frame.hex())
            await self._write_and_wait_for_opcode(client, frame, expected_opcode)
            if expected_opcode == 0x130E:
                await asyncio.sleep(_QUERY_SETTLE_DELAY)
        return gdansk_state_to_enki_payload(self._state)

    async def _async_apply_changes(
        self,
        client: Any,
        *,
        power: bool | None,
        brightness_pct: int | None,
        color_temp_kelvin: int | None,
        hs_color: tuple[float, float] | None,
    ) -> dict[str, Any]:
        if power is not None:
            frame = build_power_frame(power)
            LOGGER.debug("GDANSK BLE power frame=%s", frame.hex())
            await self._write_and_wait_for_opcode(client, frame, 0x1003)
            self._state.power = power

        if brightness_pct is not None:
            frame = build_brightness_frame(brightness_pct)
            LOGGER.debug("GDANSK BLE brightness frame=%s", frame.hex())
            await self._write_and_wait_for_opcode(client, frame, 0x1103)

        if color_temp_kelvin is not None:
            frame = build_color_temp_frame(color_temp_kelvin)
            LOGGER.debug("GDANSK BLE color-temp frame=%s", frame.hex())
            await self._write_and_wait_for_opcode(client, frame, 0x1203)
            self._state.color_mode = "ct"

        if hs_color is not None:
            frame = build_hs_frame(*hs_color)
            LOGGER.debug("GDANSK BLE hs frame=%s", frame.hex())
            await self._write_and_wait_for_opcode(client, frame, 0x1309)
            self._state.color_mode = "hs"

        return await self._async_query_state(client)

    async def _write_and_wait_for_opcode(
        self,
        client: Any,
        frame: bytes,
        expected_opcode: int,
    ) -> bytes:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bytes] = loop.create_future()
        self._pending.setdefault(expected_opcode, []).append(future)
        await client.write_gatt_char(GDANSK_WRITE_UUID, frame, response=True)
        return await asyncio.wait_for(future, timeout=_COMMAND_TIMEOUT)

    def _handle_notification(self, _: Any, data: bytearray) -> None:
        payload = bytes(data)
        opcode = parse_notification(payload, self._state)
        if opcode is None:
            return
        LOGGER.debug("GDANSK BLE notify opcode=0x%04x payload=%s", opcode, payload.hex())
        pending = self._pending.pop(opcode, [])
        for future in pending:
            if not future.done():
                future.set_result(payload)
