"""Helpers for api-enki-command-override-prod (thermostat setpoint derogations)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

# Enki app uses timed DEROGATION overrides; HA has no duration UI yet.
DEFAULT_DEROGATION_HOURS = 24

THERMOSTAT_SETPOINT_CAPABILITY = "change_thermostat_target_temperature"
OVERRIDE_TYPE_DEROGATION = "DEROGATION"


def override_end_time_iso(*, hours: int = DEFAULT_DEROGATION_HOURS) -> str:
    """Return UTC ISO-8601 end time for a command override (APK l66 / j66)."""
    end = datetime.now(UTC) + timedelta(hours=hours)
    return end.replace(microsecond=0).isoformat().replace("+00:00", "Z")
