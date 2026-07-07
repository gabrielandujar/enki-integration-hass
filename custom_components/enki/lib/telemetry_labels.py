"""Human-readable labels for telemetry exports and GitHub issue prefills."""

from __future__ import annotations

from typing import Any

_MISSING = "—"

# Referentiel device_type → GitHub label (must exist on the repository).
_DEVICE_TYPE_GITHUB_LABELS: dict[str, str] = {
    "access_and_motorizations": "device-cover",
    "ceiling_fans": "device-fan",
    "heaters_and_pilot_wires": "device-heating",
    "inverters": "device-inverter",
    "lights": "device-light",
    "modules": "device-module",
    "remote_controls_and_switches": "device-remote",
    "sensors": "device-sensor",
}

_REASON_GITHUB_LABELS: dict[str, str] = {
    "api_read_errors": "telemetry-api-error",
    "uncovered_capabilities": "telemetry-capability-gap",
    "unsupported_device": "telemetry-unsupported",
}

# Enki ecosystem manufacturers → brand-* label slug (must exist on the repository).
_BRAND_GITHUB_LABELS: frozenset[str] = frozenset(
    {
        "brand-acova",
        "brand-edisio",
        "brand-eglo",
        "brand-envertech",
        "brand-equation",
        "brand-evology",
        "brand-inspire",
        "brand-lexman",
        "brand-nodon",
        "brand-noirot",
        "brand-sedea",
    }
)

_TELEMETRY_BASE_LABEL = "device-telemetry"

# All telemetry labels managed by scripts/sync_telemetry_labels.sh
TELEMETRY_GITHUB_LABEL_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("device-telemetry", "6f42c1", "Opt-in anonymized device profile from Home Assistant"),
    ("telemetry-unsupported", "d73a4a", "Device type not supported yet"),
    ("telemetry-capability-gap", "fbca04", "Supported device with missing referentiel capabilities"),
    ("telemetry-api-error", "b60205", "Cloud API read failures on supported device"),
    ("device-cover", "1d76db", "Roller shutters and motorizations"),
    ("device-remote", "0e8a16", "Remotes, wall switches, and button triggers"),
    ("device-fan", "1d76db", "Ceiling fans and airflow"),
    ("device-heating", "b60205", "Radiators, pilot wire, thermostats"),
    ("device-light", "fef2c0", "Lights and dimmers"),
    ("device-sensor", "c5def5", "Environment and security sensors"),
    ("device-module", "bfdadc", "Outlets, relays, and power modules"),
    ("device-inverter", "006b75", "Solar inverters and production"),
    ("brand-lexman", "ededed", "Lexman hardware"),
    ("brand-inspire", "ededed", "Inspire hardware"),
    ("brand-equation", "ededed", "Equation hardware"),
    ("brand-noirot", "ededed", "Noirot hardware"),
    ("brand-eglo", "ededed", "Eglo hardware"),
    ("brand-edisio", "ededed", "Edisio hardware"),
    ("brand-evology", "ededed", "Evology hardware"),
    ("brand-nodon", "ededed", "Nodon hardware"),
    ("brand-sedea", "ededed", "Sedea hardware"),
    ("brand-envertech", "ededed", "Envertech hardware"),
    ("brand-acova", "ededed", "ACOVA hardware"),
)

_DEVICE_TYPE_LABELS: dict[str, str] = {
    "access_and_motorizations": "motorization",
    "ceiling_fans": "ceiling fan",
    "heaters_and_pilot_wires": "heating",
    "inverters": "inverter",
    "lights": "light",
    "modules": "module",
    "remote_controls_and_switches": "remote control",
    "sensors": "sensor",
}

_REASON_TITLE: dict[str, str] = {
    "api_read_errors": "API read errors",
    "uncovered_capabilities": "capability gap",
    "unsupported_device": "unsupported",
}


def humanize_device_type(device_type: str | None) -> str:
    if not device_type:
        return "device"
    normalized = device_type.strip().lower()
    if normalized in _DEVICE_TYPE_LABELS:
        return _DEVICE_TYPE_LABELS[normalized]
    return normalized.replace("_", " ")


def resolve_manufacturer_label(export: dict[str, Any]) -> str:
    manufacturer = export.get("manufacturer")
    if isinstance(manufacturer, str) and manufacturer.strip():
        return manufacturer.strip().title()
    return "Enki"


def resolve_model_label(export: dict[str, Any]) -> str:
    model = export.get("model")
    if isinstance(model, str) and model.strip() and model.strip().lower() not in {
        "unknown",
        "none",
        "n/a",
    }:
        return model.strip()

    referentiel_device_id = export.get("referentiel_device_id")
    if isinstance(referentiel_device_id, str) and referentiel_device_id.strip():
        return f"ref {referentiel_device_id.strip()[:12]}"

    capability_count = len(export.get("capabilities") or [])
    if capability_count:
        return f"{capability_count} capabilities"

    return humanize_device_type(str(export.get("device_type") or "device"))


def resolve_display_value(value: object, *, fallback: str = _MISSING) -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lower() in {"unknown", "none", "n/a"}:
            return fallback
        return stripped
    return str(value)


def telemetry_issue_reason(export: dict[str, Any]) -> str:
    reason_key = export.get("telemetry_reason")
    if isinstance(reason_key, str) and reason_key in _REASON_TITLE:
        return _REASON_TITLE[reason_key]
    if export.get("supported_by_integration"):
        return _REASON_TITLE["uncovered_capabilities"]
    return _REASON_TITLE["unsupported_device"]


def format_telemetry_issue_title(export: dict[str, Any]) -> str:
    manufacturer = resolve_manufacturer_label(export)
    device_kind = humanize_device_type(str(export.get("device_type") or ""))
    detail = resolve_model_label(export)
    reason = telemetry_issue_reason(export)

    if detail == device_kind:
        headline = f"{manufacturer} {device_kind}"
    else:
        headline = f"{manufacturer} {device_kind} · {detail}"

    return f"[telemetry] {headline} — {reason}"


def format_telemetry_notification_summary(export: dict[str, Any]) -> str:
    manufacturer = resolve_manufacturer_label(export)
    device_kind = humanize_device_type(str(export.get("device_type") or ""))
    detail = resolve_model_label(export)
    if detail == device_kind:
        return f"{manufacturer} {device_kind}"
    return f"{manufacturer} {device_kind} · {detail}"


def _brand_github_label(manufacturer: object) -> str | None:
    if not isinstance(manufacturer, str) or not manufacturer.strip():
        return None
    slug = manufacturer.strip().lower().replace(" ", "-")
    label = f"brand-{slug}"
    if label in _BRAND_GITHUB_LABELS:
        return label
    return None


def telemetry_github_labels(export: dict[str, Any]) -> tuple[str, ...]:
    """GitHub labels to pre-fill on a telemetry issue (labels must exist on the repo)."""
    labels: list[str] = [_TELEMETRY_BASE_LABEL]

    reason_key = export.get("telemetry_reason")
    if isinstance(reason_key, str) and reason_key in _REASON_GITHUB_LABELS:
        labels.append(_REASON_GITHUB_LABELS[reason_key])
    elif export.get("supported_by_integration"):
        labels.append(_REASON_GITHUB_LABELS["uncovered_capabilities"])
    else:
        labels.append(_REASON_GITHUB_LABELS["unsupported_device"])

    device_type = str(export.get("device_type") or "").strip().lower()
    if platform_label := _DEVICE_TYPE_GITHUB_LABELS.get(device_type):
        labels.append(platform_label)

    if brand_label := _brand_github_label(export.get("manufacturer")):
        labels.append(brand_label)

    return tuple(dict.fromkeys(labels))
