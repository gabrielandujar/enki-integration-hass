"""Enki cloud API client (Leroy Merlin / Adeo)."""

from __future__ import annotations

from typing import Any

import aiohttp

from ..const import DEVICE_TYPE_LIGHTS, LOGGER
from ..domain.models import EnkiDevice, EnkiDiscoveryRecord
from ..domain.profile import build_discovery_record, integration_supports_device
from ..exceptions import EnkiApiNotFoundError, EnkiConnectionError
from ..lib.bff import parse_bff_power
from ..lib.conversion import (
    direction_to_enki_rotation,
    enki_rotation_to_direction,
    merge_light_state_payload,
    normalize_power_state,
)
from .auth import EnkiAuthSession
from .transport import EnkiHttpClient


class EnkiAPI:
    """Async facade over Enki REST micro-services.

    Composes :class:`EnkiAuthSession` (OAuth) and :class:`EnkiHttpClient`
    (per-domain HTTP). Platform modules call the public ``async_*`` methods;
    discovery and state refresh stay internal.
    """

    def __init__(self, username: str, password: str) -> None:
        self._auth = EnkiAuthSession(username, password)
        self._session: aiohttp.ClientSession | None = None
        self._http: EnkiHttpClient | None = None
        self._discovery_records: list[EnkiDiscoveryRecord] = []

    async def async_close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._http = None

    async def _ensure_token(self) -> None:
        """Ensure a valid OAuth token (refresh, then password grant)."""
        http = await self._get_http()
        await http.ensure_token()

    async def _get_http(self) -> EnkiHttpClient:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
            self._http = EnkiHttpClient(self._auth, self._session)
        assert self._http is not None
        return self._http

    async def async_connect(self) -> None:
        """Authenticate with Keycloak (resource-owner password grant)."""
        http = await self._get_http()
        await self._auth.connect(http.session)

    async def async_get_devices(self) -> list[EnkiDevice]:
        """Discover all nodes across every home on the account."""
        http = await self._get_http()
        homes = await http.get_homes()
        devices: list[EnkiDevice] = []
        self._discovery_records = []
        for home_id in homes:
            home_devices, records = await self._discover_home(http, home_id)
            devices.extend(home_devices)
            self._discovery_records.extend(records)
        return devices

    @property
    def discovery_records(self) -> list[EnkiDiscoveryRecord]:
        return list(self._discovery_records)

    async def _discover_home(
        self,
        http: EnkiHttpClient,
        home_id: str,
    ) -> tuple[list[EnkiDevice], list[EnkiDiscoveryRecord]]:
        dashboard = await http.get_dashboard(home_id)
        devices: list[EnkiDevice] = []
        records: list[EnkiDiscoveryRecord] = []

        for section in dashboard.get("sections", []):
            for item in section.get("items", []):
                device, record = await self._discover_dashboard_item(http, home_id, item)
                if record is not None:
                    records.append(record)
                if device is not None:
                    devices.append(device)
        return devices, records

    async def _discover_dashboard_item(
        self,
        http: EnkiHttpClient,
        home_id: str,
        item: dict[str, Any],
    ) -> tuple[EnkiDevice | None, EnkiDiscoveryRecord | None]:
        metadata = item.get("metadata", {})
        if "nodeId" not in metadata:
            return None, None

        node_id = metadata["nodeId"]
        device_id = metadata["deviceId"]
        bff_type = metadata.get("deviceType", "")
        main_change_capability = metadata.get("mainChangeCapability") or {}
        main_change_endpoints = [
            endpoint.get("id")
            for endpoint in main_change_capability.get("endpoints", [])
            if endpoint.get("id") is not None
        ]

        node_info = await http.get_node(home_id, node_id)
        device_info = await http.get_referentiel_device(device_id)
        device_type = device_info.get("type") or bff_type
        capabilities = device_info.get("capabilities", [])
        possible_values = device_info.get("possibleValues", {})
        power_production = parse_bff_power(item.get("description"))

        skeleton = EnkiDevice(
            home_id=home_id,
            device_id=device_id,
            node_id=node_id,
            device_name=item["title"]["label"],
            device_type=device_type,
            is_enabled=item["isEnabled"],
            state=item["state"],
            capabilities=capabilities,
            possible_values=possible_values,
            bff_device_type=bff_type,
            main_change_capability_id=metadata.get("mainChangeCapabilityId"),
            main_change_capability_endpoints=main_change_endpoints,
            power_production=power_production,
        )
        supported = integration_supports_device(skeleton)

        manufacturer = (
            node_info.get("manufacturerId")
            or device_info.get("manufacturerId")
            or device_info.get("manufacturer")
        )
        model = node_info.get("modelNumber") or device_info.get("modelNumber")
        firmware = node_info.get("version") or device_info.get("version")

        record = build_discovery_record(
            device_type=device_type,
            bff_device_type=bff_type,
            capabilities=capabilities,
            possible_values=possible_values,
            manufacturer=str(manufacturer) if manufacturer else None,
            model=str(model) if model else None,
            firmware_version=str(firmware) if firmware else None,
            supported_by_integration=supported,
        )

        last_reported: dict[str, Any] = {}
        if item["isEnabled"]:
            last_reported = await self._refresh_device_state(http, skeleton, node_info)

        if not supported:
            LOGGER.debug(
                "Skipping unsupported Enki device type %s (%s)",
                device_type,
                item.get("title", {}).get("label"),
            )
            return None, record

        return (
            EnkiDevice(
                home_id=home_id,
                device_id=device_id,
                node_id=node_id,
                device_name=item["title"]["label"],
                device_type=device_type,
                is_enabled=item["isEnabled"],
                state=item["state"],
                capabilities=capabilities,
                possible_values=possible_values,
                last_reported_value={**node_info, **last_reported},
                bff_device_type=bff_type,
                main_change_capability_id=metadata.get("mainChangeCapabilityId"),
                main_change_capability_endpoints=main_change_endpoints,
                power_production=power_production,
            ),
            record,
        )

    async def _refresh_device_state(
        self,
        http: EnkiHttpClient,
        device: EnkiDevice,
        node_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Load live state based on referentiel capabilities (not only device type)."""
        profile = device.profile
        home_id = device.home_id
        node_id = device.node_id

        if profile.is_fan:
            return await self._read_fan_state(http, home_id, node_id)

        state: dict[str, Any] = {}

        if profile.supports_light_state or device.device_type == DEVICE_TYPE_LIGHTS:
            try:
                light_state = await self._read_light_payload(http, home_id, node_id)
                state.update(light_state)
                if light_state.get("power"):
                    state["light_power"] = light_state["power"]
            except EnkiConnectionError as err:
                LOGGER.debug("Light state skipped for node %s: %s", node_id, err)

        if profile.supports_electrical_power:
            try:
                power_details = await http.get_electrical_power(home_id, node_id)
                state["electrical_power"] = power_details.get("lastReportedValue")
                state["electrical_endpoints"] = power_details.get("endpoints", [])
                if not state.get("power") and isinstance(state["electrical_power"], str):
                    state["power"] = state["electrical_power"]
            except EnkiConnectionError as err:
                LOGGER.debug("Electrical power skipped for node %s: %s", node_id, err)

        if profile.supports_fan_speed:
            try:
                data = await http.airflow_get(home_id, node_id, "check-fan-speed")
                state["fan_speed"] = data["lastReportedValue"]
            except EnkiConnectionError as err:
                LOGGER.debug("Fan speed skipped for node %s: %s", node_id, err)

        if profile.supports_airflow_mode:
            try:
                data = await http.airflow_get(home_id, node_id, "check-airflow-mode")
                state["airflow_mode"] = data["lastReportedValue"]
            except EnkiConnectionError as err:
                LOGGER.debug("Airflow mode skipped for node %s: %s", node_id, err)

        if profile.is_inverter:
            state["power_production"] = device.power_production

        return state

    async def _read_fan_state(
        self,
        http: EnkiHttpClient,
        home_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        speed_data = await http.airflow_get(home_id, node_id, "check-fan-speed")
        mode_data = await http.airflow_get(home_id, node_id, "check-airflow-mode")
        rotation, rotation_supported = await self._read_fan_rotation(http, home_id, node_id)
        light_state = await http.get_light_state(home_id, node_id)
        last_reported = light_state.get("lastReportedValue", {})
        light_power = last_reported.get("power", "OFF")

        state: dict[str, Any] = {
            "fan_speed": speed_data["lastReportedValue"],
            "airflow_mode": mode_data["lastReportedValue"],
            "airflow_rotation": rotation,
            "airflow_rotation_supported": rotation_supported,
            "light_power": light_power,
            "brightness": last_reported.get("brightness"),
            "colorTemperature": last_reported.get("colorTemperature"),
            "power": last_reported.get("power"),
        }
        try:
            power_details = await http.get_electrical_power(home_id, node_id)
            state["electrical_power"] = power_details.get("lastReportedValue")
            state["electrical_endpoints"] = power_details.get("endpoints", [])
        except EnkiConnectionError as err:
            LOGGER.debug("Electrical power skipped for fan node %s: %s", node_id, err)
        return state

    async def _read_fan_rotation(
        self,
        http: EnkiHttpClient,
        home_id: str,
        node_id: str,
    ) -> tuple[str | None, bool]:
        """Best-effort rotation read; optional probes must not fail discovery."""
        try:
            data = await http.airflow_get(home_id, node_id, "check-fan-rotation-direction")
        except (EnkiApiNotFoundError, EnkiConnectionError) as err:
            LOGGER.debug(
                "Optional airflow check-fan-rotation-direction for node %s skipped: %s",
                node_id,
                err,
            )
            return None, False
        direction = enki_rotation_to_direction(data.get("lastReportedValue"))
        return direction, True

    async def _read_light_payload(
        self,
        http: EnkiHttpClient,
        home_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        state = await http.get_light_state(home_id, node_id)
        return state.get("lastReportedValue", {})

    # --- public command API --------------------------------------------------

    async def async_switch_electrical_power(
        self,
        home_id: str,
        node_id: str,
        value: str,
    ) -> None:
        """Switch global electrical power (sockets, outlets without lighting API)."""
        http = await self._get_http()
        await http.switch_electrical_power(home_id, node_id, value)

    async def async_set_fan_rotation(
        self,
        home_id: str,
        node_id: str,
        direction: str,
    ) -> None:
        """Set blade rotation via change-fan-rotation-direction."""
        http = await self._get_http()
        enki_value = direction_to_enki_rotation(direction)
        await http.airflow_post(home_id, node_id, "change-fan-rotation-direction", enki_value)

    async def async_set_airflow_mode(self, home_id: str, node_id: str, mode: str) -> None:
        """Set ventilation mode (MANUAL / BREEZE)."""
        http = await self._get_http()
        await http.airflow_post(home_id, node_id, "change-airflow-mode", mode)

    async def async_set_fan_speed(self, home_id: str, node_id: str, speed: int) -> None:
        """Set fan speed (0 = off, 1–6 = levels)."""
        http = await self._get_http()
        await http.airflow_post(home_id, node_id, "change-fan-speed", speed)

    async def async_set_light_power(self, home_id: str, node_id: str, on: bool) -> None:
        """Turn the ESDK fan light kit on or off (lighting API)."""
        await self.async_change_light_state(
            home_id,
            node_id,
            {"power": "ON" if on else "OFF"},
        )

    async def async_change_light_state(
        self,
        home_id: str,
        node_id: str,
        changes: dict[str, Any],
    ) -> None:
        """Apply one or more lighting fields in a single change-light-state call."""
        http = await self._get_http()
        current = await http.get_light_state(home_id, node_id)
        payload = merge_light_state_payload(
            current.get("lastReportedValue", {}),
            changes,
        )
        await http.change_light_state(home_id, node_id, payload)

    async def async_change_light_state_field(
        self,
        home_id: str,
        node_id: str,
        parameter: str,
        value: Any,
    ) -> None:
        """Backward-compatible wrapper for single-field lighting updates."""
        await self.async_change_light_state(home_id, node_id, {parameter: value})

    async def _get_power_state(self, home_id: str, node_id: str, endpoint: int) -> str:
        """Read one endpoint power state (used by integration tests)."""
        http = await self._get_http()
        data = await http.get_electrical_power(home_id, node_id)
        return normalize_power_state(data.get("lastReportedValue"), endpoint)
