"""Unit tests for airflow mode API commands."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from enki.api import EnkiAPI
from enki.const import AIRFLOW_MODE_BREEZE


@pytest.mark.asyncio
async def test_set_airflow_mode_uses_change_airflow_mode() -> None:
    api = EnkiAPI("user", "pass")
    api._ensure_token = AsyncMock()  # type: ignore[method-assign]
    api._airflow_post = AsyncMock()  # type: ignore[method-assign]

    await api.async_set_airflow_mode("home", "node", AIRFLOW_MODE_BREEZE)

    api._airflow_post.assert_awaited_once_with(
        "home",
        "node",
        "change-airflow-mode",
        AIRFLOW_MODE_BREEZE,
    )
