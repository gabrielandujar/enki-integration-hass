"""Anonymized Enki device profiles for telemetry and diagnostics."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .const import DEVICE_TYPE_FANS, DEVICE_TYPE_LIGHTS
from .models import EnkiDiscoveryRecord

SUPPORTED_DEVICE_TYPES = {DEVICE_TYPE_FANS, DEVICE_TYPE_LIGHTS}

_SENSITIVE_STATE_KEYS = frozenset(
    {
        "homeId",
        "home_id",
        "nodeId",
        "node_id",
        "deviceId",
        "device_id",
        "deviceName",
        "device_name",
        "title",
        "email",
        "username",
    }
)


def _sanitize_possible_values(values: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in values.items():
        if not isinstance(key, str):
            continue
        if isinstance(value, dict):
            entry = {k: v for k, v in value.items() if k in {"values", "type", "min", "max"}}
            if entry:
                sanitized[key] = entry
        elif isinstance(value, list):
            sanitized[key] = value
    return sanitized


def build_discovery_record(
    *,
    device_type: str,
    bff_device_type: str,
    capabilities: list[str],
    possible_values: dict[str, Any],
    manufacturer: str | None,
    model: str | None,
    firmware_version: str | None,
    supported_by_integration: bool,
) -> EnkiDiscoveryRecord:
    return EnkiDiscoveryRecord(
        device_type=device_type,
        bff_device_type=bff_device_type,
        capabilities=list(capabilities),
        possible_values=_sanitize_possible_values(possible_values),
        manufacturer=manufacturer,
        model=model,
        firmware_version=firmware_version,
        supported_by_integration=supported_by_integration,
    )


def profile_to_export_dict(
    record: EnkiDiscoveryRecord,
    *,
    integration_version: str,
    ha_version: str,
) -> dict[str, Any]:
    return {
        "device_type": record.device_type,
        "bff_device_type": record.bff_device_type,
        "manufacturer": record.manufacturer,
        "model": record.model,
        "firmware_version": record.firmware_version,
        "supported_by_integration": record.supported_by_integration,
        "capabilities": sorted(record.capabilities),
        "possible_values": record.possible_values,
        "integration_version": integration_version,
        "ha_version": ha_version,
    }


def profile_fingerprint(export_dict: dict[str, Any]) -> str:
    """Stable hash for deduplication (excludes integration/HA version)."""
    stable = {
        "device_type": export_dict.get("device_type"),
        "bff_device_type": export_dict.get("bff_device_type"),
        "manufacturer": export_dict.get("manufacturer"),
        "model": export_dict.get("model"),
        "firmware_version": export_dict.get("firmware_version"),
        "supported_by_integration": export_dict.get("supported_by_integration"),
        "capabilities": export_dict.get("capabilities"),
        "possible_values": export_dict.get("possible_values"),
    }
    payload = json.dumps(stable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def format_github_issue_body(export_dict: dict[str, Any], fingerprint: str) -> str:
    supported = "oui" if export_dict.get("supported_by_integration") else "non"
    capabilities = export_dict.get("capabilities") or []
    possible_values = export_dict.get("possible_values") or {}

    cap_lines = "\n".join(f"- `{capability}`" for capability in capabilities) or "- _(aucune)_"

    return (
        "## Profil appareil Enki (télémétrie opt-in)\n\n"
        "Rapport automatique — données anonymisées, sans identifiant de compte ou de domicile.\n\n"
        f"- **Type référentiel** : `{export_dict.get('device_type', 'unknown')}`\n"
        f"- **Type BFF** : `{export_dict.get('bff_device_type', '')}`\n"
        f"- **Fabricant** : {export_dict.get('manufacturer') or 'inconnu'}\n"
        f"- **Modèle** : {export_dict.get('model') or 'inconnu'}\n"
        f"- **Firmware** : {export_dict.get('firmware_version') or 'inconnu'}\n"
        f"- **Supporté par l'intégration** : {supported}\n"
        f"- **Version intégration** : `{export_dict.get('integration_version', '')}`\n"
        f"- **Home Assistant** : `{export_dict.get('ha_version', '')}`\n"
        f"- **Empreinte** : `{fingerprint[:16]}`\n\n"
        "### Capabilities\n"
        f"{cap_lines}\n\n"
        "### Possible values\n"
        f"```json\n{json.dumps(possible_values, indent=2, sort_keys=True)}\n```\n"
    )


def format_github_issue_title(export_dict: dict[str, Any]) -> str:
    device_type = export_dict.get("device_type", "unknown")
    model = export_dict.get("model") or "unknown"
    if export_dict.get("supported_by_integration"):
        return f"[telemetry] Profil {device_type} — {model}"
    return f"[telemetry] Appareil non supporté — {device_type} ({model})"
