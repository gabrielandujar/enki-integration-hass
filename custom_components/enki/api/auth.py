"""OAuth session management for the Enki Keycloak realm."""

from __future__ import annotations

import time
from typing import Any

import aiohttp

from ..const import ENKI_OIDC_URL, LOGGER
from ..exceptions import EnkiAuthError, EnkiConnectionError


class EnkiAuthSession:
    """Maintains access and refresh tokens for Enki cloud APIs.

    Tokens are renewed via refresh_token when possible, falling back to the
    resource-owner password grant only when refresh fails (#44).
    """

    _TOKEN_SKEW_SECONDS = 30

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_type = "Bearer"
        self._token_expires_at = 0.0

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def token_type(self) -> str:
        return self._token_type

    def is_valid(self) -> bool:
        return (
            bool(self._access_token)
            and time.time() < self._token_expires_at - self._TOKEN_SKEW_SECONDS
        )

    def auth_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Build Authorization header; call ``ensure_valid`` first."""
        headers = {"Authorization": f"{self._token_type} {self._access_token}"}
        if extra:
            headers.update(extra)
        return headers

    async def ensure_valid(self, session: aiohttp.ClientSession) -> None:
        """Refresh or re-authenticate when the access token is near expiry."""
        if self.is_valid():
            return
        if self._refresh_token:
            try:
                await self.refresh(session)
                return
            except EnkiAuthError:
                LOGGER.debug("Refresh token rejected, falling back to password grant")
        await self.connect(session)

    async def connect(self, session: aiohttp.ClientSession) -> None:
        """Authenticate with Keycloak (resource-owner password grant)."""
        payload = await self._token_request(
            session,
            {
                "grant_type": "password",
                "client_id": "enki-front",
                "username": self._username,
                "password": self._password,
            },
        )
        if payload is None:
            raise EnkiAuthError("Invalid username or password")
        self._apply_token_payload(payload)
        LOGGER.debug("Enki session established, expires in %ss", payload["expires_in"])

    async def refresh(self, session: aiohttp.ClientSession) -> None:
        """Renew the access token without sending the account password again."""
        if not self._refresh_token:
            raise EnkiAuthError("No refresh token available")
        payload = await self._token_request(
            session,
            {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": "enki-front",
            },
        )
        if payload is None:
            raise EnkiAuthError("Token refresh rejected")
        self._apply_token_payload(payload)
        LOGGER.debug("Enki token refreshed, expires in %ss", payload["expires_in"])

    def _apply_token_payload(self, payload: dict[str, Any]) -> None:
        self._access_token = payload["access_token"]
        self._token_type = payload.get("token_type", "Bearer")
        self._token_expires_at = time.time() + payload["expires_in"]
        if refreshed := payload.get("refresh_token"):
            self._refresh_token = refreshed

    async def _token_request(
        self,
        session: aiohttp.ClientSession,
        data: dict[str, str],
    ) -> dict[str, Any] | None:
        try:
            async with session.post(
                ENKI_OIDC_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
            ) as response:
                if response.status == 401:
                    return None
                if response.status != 200:
                    raise EnkiConnectionError(f"Authentication failed: HTTP {response.status}")
                return await response.json()
        except aiohttp.ClientError as err:
            raise EnkiConnectionError(f"Cannot reach Enki auth: {err}") from err
