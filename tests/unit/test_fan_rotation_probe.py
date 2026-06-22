"""Unit tests for optional fan rotation API probing."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from enki.api import EnkiAPI
from enki.const import DIRECTION_FORWARD
from enki.exceptions import EnkiConnectionError


@pytest.mark.asyncio
async def test_get_fan_rotation_ignores_http_500_on_probe() -> None:
    api = EnkiAPI("user", "pass")
    api._try_airflow_get = AsyncMock(return_value=None)  # type: ignore[method-assign]

    rotation, supported = await api._get_fan_rotation("home", "node")

    assert rotation is None
    assert supported is False


@pytest.mark.asyncio
async def test_get_fan_rotation_reads_fan_rotation_direction() -> None:
    api = EnkiAPI("user", "pass")
    api._try_airflow_get = AsyncMock(  # type: ignore[method-assign]
        return_value={"lastReportedValue": "CLOCKWISE"}
    )

    rotation, supported = await api._get_fan_rotation("home", "node")

    assert rotation == DIRECTION_FORWARD
    assert supported is True
