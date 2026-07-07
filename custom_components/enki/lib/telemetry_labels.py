"""Human-readable labels for telemetry exports and GitHub issue prefills."""

from __future__ import annotations

from typing import Any

_MISSING = "—"

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
