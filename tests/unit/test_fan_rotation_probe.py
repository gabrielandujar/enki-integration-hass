"""Unit tests for optional fan rotation API probing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from enki.api import EnkiAPI
from enki.exceptions import EnkiConnectionError


@pytest.mark.asyncio
async def test_get_fan_rotation_ignores_http_500_on_probe() -> None:
    api = EnkiAPI("user", "pass")
    api._airflow_get = AsyncMock(  # type: ignore[method-assign]
        side_effect=EnkiConnectionError("check-airflow-rotation failed: HTTP 500", status=500)
    )

    rotation, supported = await api._get_fan_rotation("home", "node", "MANUAL")

    assert rotation is None
    assert supported is False
