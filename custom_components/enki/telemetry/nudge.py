"""One-time telemetry opt-in nudge for legacy installs (pre-1.0.6)."""

from __future__ import annotations

from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..const import CONF_TELEMETRY, CONF_TELEMETRY_ONBOARDING, DOMAIN, LOGGER

STORAGE_VERSION = 1
TELEMETRY_NUDGE_LEGACY_VERSION = "1.0.6"
NOTIFICATION_ID_PREFIX = f"{DOMAIN}_telemetry_nudge"


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a semver-like string into comparable integer parts."""
    parts: list[int] = []
    for segment in version.replace("-", ".").split("."):
        if segment.isdigit():
            parts.append(int(segment))
        elif segment:
            break
    return tuple(parts or [0])


def version_is_before(version: str, reference: str) -> bool:
    """Return True when version sorts strictly before reference."""
    left = parse_version(version)
    right = parse_version(reference)
    length = max(len(left), len(right))
    return left + (0,) * (length - len(left)) < right + (0,) * (length - len(right))


class EnkiTelemetryNudge:
    """Show a single settings notification encouraging telemetry for legacy users."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.install_meta.{entry.entry_id}",
        )

    async def async_handle_setup(self) -> None:
        """Record install metadata and maybe show the legacy nudge once."""
        meta = await self._load_meta()

        if self._entry.options.get(CONF_TELEMETRY):
            await self._dismiss_notification()
            if not meta.get("telemetry_nudge_dismissed"):
                meta["telemetry_nudge_dismissed"] = True
                await self._save_meta(meta)
            return

        if self._entry.options.get(CONF_TELEMETRY_ONBOARDING):
            meta.setdefault("first_seen_version", await self._integration_version())
            meta["telemetry_nudge_dismissed"] = True
            await self._save_meta(meta)
            return

        if meta.get("telemetry_nudge_dismissed"):
            return

        if not meta.get("first_seen_version"):
            meta["first_seen_version"] = "legacy"
            await self._save_meta(meta)

        if not self._should_nudge_legacy(meta):
            return

        await self._show_notification()
        meta["telemetry_nudge_dismissed"] = True
        await self._save_meta(meta)
        LOGGER.debug(
            "Showed one-time telemetry nudge for Enki entry %s",
            self._entry.entry_id,
        )

    def _should_nudge_legacy(self, meta: dict[str, Any]) -> bool:
        first_seen = str(meta.get("first_seen_version", "legacy"))
        if first_seen == "legacy":
            return True
        return version_is_before(first_seen, TELEMETRY_NUDGE_LEGACY_VERSION)

    async def _show_notification(self) -> None:
        title, message = _nudge_copy(self._hass, self._entry.entry_id)
        await persistent_notification.async_create(
            self._hass,
            title=title,
            message=message,
            notification_id=f"{NOTIFICATION_ID_PREFIX}_{self._entry.entry_id}",
        )

    async def _dismiss_notification(self) -> None:
        await persistent_notification.async_dismiss(
            self._hass,
            f"{NOTIFICATION_ID_PREFIX}_{self._entry.entry_id}",
        )

    async def _load_meta(self) -> dict[str, Any]:
        return dict(await self._store.async_load() or {})

    async def _save_meta(self, meta: dict[str, Any]) -> None:
        await self._store.async_save(meta)

    async def _integration_version(self) -> str:
        from .. import __version__

        return __version__


def _nudge_copy(hass: HomeAssistant, entry_id: str) -> tuple[str, str]:
    configure_url = f"/config/integrations/configure/{entry_id}"
    if hass.config.language.startswith("fr"):
        return (
            "Enki — accélérez le support de nouveaux appareils",
            (
                "Activez la **télémétrie opt-in** pour être averti lorsqu'un appareil "
                "Enki non supporté est détecté chez vous.\n\n"
                "Données **anonymisées** (type, modèle, capabilities) — "
                "aucun envoi automatique, seulement un lien GitHub pré-rempli "
                "si vous le souhaitez.\n\n"
                "Cela aide à prioriser radiateurs, volets, prises et autres matériels.\n\n"
                f"[Ouvrir les options Enki]({configure_url})"
            ),
        )
    return (
        "Enki — help prioritize new device support",
        (
            "Turn on **opt-in telemetry** to get notified when an unsupported Enki "
            "device is detected on your account.\n\n"
            "**Anonymized** data only (type, model, capabilities) — "
            "nothing is sent automatically; you get a pre-filled GitHub link if you choose.\n\n"
            "This helps prioritize heaters, shutters, sockets, and other hardware.\n\n"
            f"[Open Enki options]({configure_url})"
        ),
    )


async def async_handle_telemetry_nudge(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entry point called once per successful setup."""
    await EnkiTelemetryNudge(hass, entry).async_handle_setup()
