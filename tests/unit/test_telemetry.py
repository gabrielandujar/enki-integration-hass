"""Unit tests for opt-in device profile notifications."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from enki.const import CONF_TELEMETRY
from enki.domain.profile import build_discovery_record
from enki.telemetry.reporter import EnkiTelemetryReporter


def _record():
    return build_discovery_record(
        device_type="equation_radiator",
        bff_device_type="radiators",
        capabilities=["check_temperature"],
        possible_values={},
        manufacturer="equation",
        model="neo",
        firmware_version=None,
        supported_by_integration=False,
    )


@pytest.mark.asyncio
async def test_telemetry_skipped_when_disabled() -> None:
    hass = MagicMock()
    hass.config.version = "2024.12.0"
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.options = {CONF_TELEMETRY: False}

    reporter = EnkiTelemetryReporter(hass, entry)
    with patch(
        "enki.telemetry.reporter.persistent_notification.async_create",
        new_callable=MagicMock,
    ) as notify:
        await reporter.async_report([_record()])
        notify.assert_not_called()


@pytest.mark.asyncio
async def test_telemetry_notifies_new_profile() -> None:
    hass = MagicMock()
    hass.config.version = "2024.12.0"
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.options = {CONF_TELEMETRY: True}

    reporter = EnkiTelemetryReporter(hass, entry)
    reporter._store.async_load = AsyncMock(return_value={"fingerprints": []})  # type: ignore[method-assign]
    reporter._store.async_save = AsyncMock()  # type: ignore[method-assign]

    with patch(
        "enki.telemetry.reporter.persistent_notification.async_create",
        new_callable=MagicMock,
    ) as notify:
        await reporter.async_report([_record()])
        notify.assert_called_once()
        reporter._store.async_save.assert_awaited()
        message = notify.call_args.kwargs["message"]
        assert "github.com" in message
        assert "equation_radiator" in message


@pytest.mark.asyncio
async def test_telemetry_dedupes_fingerprint() -> None:
    hass = MagicMock()
    hass.config.version = "2024.12.0"
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.options = {CONF_TELEMETRY: True}

    reporter = EnkiTelemetryReporter(hass, entry)
    reporter._store.async_load = AsyncMock(return_value={"fingerprints": []})  # type: ignore[method-assign]
    reporter._store.async_save = AsyncMock()  # type: ignore[method-assign]

    with patch(
        "enki.telemetry.reporter.persistent_notification.async_create",
        new_callable=MagicMock,
    ) as notify:
        await reporter.async_report([_record()])
        await reporter.async_report([_record()])
        notify.assert_called_once()


@pytest.mark.asyncio
async def test_telemetry_tolerates_corrupt_storage() -> None:
    hass = MagicMock()
    hass.config.version = "2024.12.0"
    hass.config.language = "en"
    entry = MagicMock()
    entry.entry_id = "entry1"
    entry.options = {CONF_TELEMETRY: True}

    reporter = EnkiTelemetryReporter(hass, entry)
    reporter._store.async_load = AsyncMock(return_value={"fingerprints": None})  # type: ignore[method-assign]
    reporter._store.async_save = AsyncMock()  # type: ignore[method-assign]

    with patch(
        "enki.telemetry.reporter.persistent_notification.async_create",
        new_callable=MagicMock,
    ) as notify:
        await reporter.async_report([_record()])
        notify.assert_called_once()
