"""Unit tests for Enki API authentication."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses
from enki.api import EnkiAPI
from enki.const import ENKI_OIDC_URL
from enki.exceptions import EnkiAuthError, EnkiConnectionError


@pytest.mark.asyncio
async def test_connect_success() -> None:
    with aioresponses() as mocked:
        mocked.post(
            ENKI_OIDC_URL,
            status=200,
            payload={
                "access_token": "token-abc",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )
        api = EnkiAPI("user@example.com", "secret")
        await api.async_connect()
        assert api._access_token == "token-abc"
        await api.async_close()


@pytest.mark.asyncio
async def test_connect_invalid_credentials() -> None:
    with aioresponses() as mocked:
        mocked.post(ENKI_OIDC_URL, status=401, payload={"error": "invalid_grant"})
        api = EnkiAPI("user@example.com", "wrong")
        with pytest.raises(EnkiAuthError):
            await api.async_connect()
        await api.async_close()


@pytest.mark.asyncio
async def test_connect_upstream_error() -> None:
    with aioresponses() as mocked:
        mocked.post(ENKI_OIDC_URL, status=503, payload={"error": "unavailable"})
        api = EnkiAPI("user@example.com", "secret")
        with pytest.raises(EnkiConnectionError):
            await api.async_connect()
        await api.async_close()


@pytest.mark.asyncio
async def test_connect_network_failure() -> None:
    with aioresponses() as mocked:
        mocked.post(ENKI_OIDC_URL, exception=aiohttp.ClientConnectionError("offline"))
        api = EnkiAPI("user@example.com", "secret")
        with pytest.raises(EnkiConnectionError, match="Cannot reach Enki auth"):
            await api.async_connect()
        await api.async_close()
