"""Live integration tests against the Enki cloud API.

Requires ENKI_USERNAME, ENKI_PASSWORD, ENKI_HOME_ID, ENKI_NODE_ID in the environment.
"""

from __future__ import annotations

import asyncio
import os

import pytest
from enki.api import EnkiAPI
from enki.const import DEVICE_TYPE_FANS, LIGHT_ENDPOINT
from enki.exceptions import EnkiAuthError

pytestmark = pytest.mark.integration

USERNAME = os.getenv("ENKI_USERNAME", "")
PASSWORD = os.getenv("ENKI_PASSWORD", "")
HOME_ID = os.getenv("ENKI_HOME_ID", "")
NODE_ID = os.getenv("ENKI_NODE_ID", "")

if not all([USERNAME, PASSWORD, HOME_ID, NODE_ID]):
    pytest.skip(
        "Set ENKI_USERNAME, ENKI_PASSWORD, ENKI_HOME_ID, ENKI_NODE_ID for integration tests",
        allow_module_level=True,
    )


@pytest.fixture
async def api():
    client = EnkiAPI(USERNAME, PASSWORD)
    await client.async_connect()
    yield client
    await client.async_set_fan_speed(HOME_ID, NODE_ID, 0)
    await client.async_set_light_power(HOME_ID, NODE_ID, False)
    await client.async_close()


@pytest.mark.asyncio
async def test_connect(api: EnkiAPI) -> None:
    assert api._access_token is not None


@pytest.mark.asyncio
async def test_connect_bad_password() -> None:
    client = EnkiAPI(USERNAME, "definitely-wrong-password")
    with pytest.raises(EnkiAuthError):
        await client.async_connect()
    await client.async_close()


@pytest.mark.asyncio
async def test_discover_ceiling_fan(api: EnkiAPI) -> None:
    devices = await api.async_get_devices()
    assert devices
    fan = next((device for device in devices if device.node_id == NODE_ID), None)
    assert fan is not None
    assert fan.device_type == DEVICE_TYPE_FANS


@pytest.mark.asyncio
async def test_fan_speed_control(api: EnkiAPI) -> None:
    await api.async_set_fan_speed(HOME_ID, NODE_ID, 1)
    await asyncio.sleep(2)
    speed = await api._get_fan_speed(HOME_ID, NODE_ID)
    assert speed > 0

    await api.async_set_fan_speed(HOME_ID, NODE_ID, 0)
    await asyncio.sleep(2)
    assert await api._get_fan_speed(HOME_ID, NODE_ID) == 0


@pytest.mark.asyncio
async def test_light_power_independent(api: EnkiAPI) -> None:
    await api.async_set_fan_speed(HOME_ID, NODE_ID, 1)
    await asyncio.sleep(2)
    state = await api._get_light_state(HOME_ID, NODE_ID)
    assert state["lastReportedValue"]["power"] == "OFF"

    await api.async_set_light_power(HOME_ID, NODE_ID, True)
    await asyncio.sleep(2)
    assert await api._get_power_state(HOME_ID, NODE_ID, LIGHT_ENDPOINT) == "ON"
    speed = await api._get_fan_speed(HOME_ID, NODE_ID)
    assert speed > 0
