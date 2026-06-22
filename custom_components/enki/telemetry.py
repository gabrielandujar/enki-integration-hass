"""Opt-in device telemetry via GitHub repository_dispatch."""

from __future__ import annotations

import json
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONF_TELEMETRY,
    DOMAIN,
    LOGGER,
    TELEMETRY_DISPATCH_EVENT,
    TELEMETRY_DISPATCH_TOKEN,
    TELEMETRY_GITHUB_REPO,
)
from .device_profile import profile_fingerprint, profile_to_export_dict
from .models import EnkiDiscoveryRecord

STORAGE_VERSION = 1


class EnkiTelemetryReporter:
    """Report anonymized device profiles once per unique fingerprint."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.telemetry.{entry.entry_id}",
        )
        self._reported: set[str] | None = None

    async def async_report(self, records: list[EnkiDiscoveryRecord]) -> None:
        if not self._entry.options.get(CONF_TELEMETRY, False):
            return
        if not TELEMETRY_DISPATCH_TOKEN:
            LOGGER.debug("Enki telemetry enabled but TELEMETRY_DISPATCH_TOKEN is not configured")
            return
        if not records:
            return

        reported = await self._load_reported()
        integration_version = await self._integration_version()
        ha_version = self._hass.config.version

        pending_exports: list[dict[str, Any]] = []
        for record in records:
            export_dict = profile_to_export_dict(
                record,
                integration_version=integration_version,
                ha_version=ha_version,
            )
            fingerprint = profile_fingerprint(export_dict)
            if fingerprint in reported:
                continue
            export_dict["fingerprint"] = fingerprint
            pending_exports.append(export_dict)
            reported.add(fingerprint)

        if not pending_exports:
            return

        try:
            await self._dispatch_profiles(pending_exports)
        except Exception:
            LOGGER.exception("Failed to submit Enki device telemetry")
            return

        await self._save_reported(reported)
        LOGGER.info(
            "Submitted %s new Enki device profile(s) via telemetry",
            len(pending_exports),
        )

    async def _load_reported(self) -> set[str]:
        if self._reported is not None:
            return self._reported
        data = await self._store.async_load() or {}
        fingerprints = data.get("fingerprints", [])
        self._reported = {str(item) for item in fingerprints}
        return self._reported

    async def _save_reported(self, reported: set[str]) -> None:
        self._reported = reported
        await self._store.async_save({"fingerprints": sorted(reported)})

    async def _integration_version(self) -> str:
        from . import __version__

        return __version__

    async def _dispatch_profiles(self, profiles: list[dict[str, Any]]) -> None:
        owner, repo = TELEMETRY_GITHUB_REPO.split("/", 1)
        url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
        headers = {
            "Authorization": f"Bearer {TELEMETRY_DISPATCH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "event_type": TELEMETRY_DISPATCH_EVENT,
            "client_payload": {
                "profiles_json": json.dumps(profiles, separators=(",", ":")),
            },
        }
        timeout = aiohttp.ClientTimeout(total=30)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                url,
                headers=headers,
                json=payload,
            ) as response,
        ):
            if response.status == 204:
                return
            body = await response.text()
            raise RuntimeError(
                f"GitHub repository_dispatch failed: HTTP {response.status} — {body}"
            )
