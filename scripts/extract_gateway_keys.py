#!/usr/bin/env python3
"""Extract Enki X-Gateway-APIKey values from an Android APK.

Usage:
    python scripts/extract_gateway_keys.py path/to/enki.apk

The script scans DEX/assets for api-enki-*-prod service names and 32-char
gateway key candidates, then cross-checks against keys already in const.py.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONST_PY = REPO_ROOT / "custom_components" / "enki" / "const.py"

# Micro-service slug in URL -> const.py symbol
SERVICE_MAP: dict[str, str] = {
    "api-enki-home-prod": "ENKI_HOME_API_KEY",
    "api-enki-mobile-bff-prod": "ENKI_BFF_API_KEY",
    "api-enki-node-agg-prod": "ENKI_NODE_API_KEY",
    "api-enki-referentiel-agg-prod": "ENKI_REFERENTIEL_API_KEY",
    "api-enki-lighting-prod": "ENKI_LIGHTS_API_KEY",
    "api-enki-power-prod": "ENKI_POWER_API_KEY",
    "api-enki-airflow-prod": "ENKI_AIRFLOW_API_KEY",
    "api-enki-temperature-humidity-sensor-prod": "ENKI_TEMPERATURE_HUMIDITY_API_KEY",
    "api-enki-battery-health-prod": "ENKI_BATTERY_HEALTH_API_KEY",
    "api-enki-presence-detector-prod": "ENKI_PRESENCE_DETECTOR_API_KEY",
    "api-enki-contact-sensor-prod": "ENKI_CONTACT_SENSOR_API_KEY",
    "api-enki-siren-prod": "ENKI_SIREN_API_KEY",
    "api-enki-heating-prod": "ENKI_HEATING_API_KEY",
    "api-enki-water-leak-detector-prod": "ENKI_WATER_SENSOR_API_KEY",
    "api-enki-water-sensor-prod": "ENKI_WATER_SENSOR_API_KEY",
    "api-enki-rolling-prod": "ENKI_ACCESS_MOTORIZATION_API_KEY",
    "api-enki-access-and-motorizations-prod": "ENKI_ACCESS_MOTORIZATION_API_KEY",
}

KEY_PATTERN = re.compile(r"\b[A-Za-z0-9]{32}\b")
ASSIGN_PATTERN = re.compile(r'^(ENKI_[A-Z_]+)\s*=\s*"([^"]*)"')

MISSING_TARGETS = frozenset(
    {
        "ENKI_HEATING_API_KEY",
        "ENKI_WATER_SENSOR_API_KEY",
        "ENKI_ACCESS_MOTORIZATION_API_KEY",
    }
)


def read_const_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    for line in CONST_PY.read_text(encoding="utf-8").splitlines():
        match = ASSIGN_PATTERN.match(line.strip())
        if match and match.group(1).endswith("_API_KEY"):
            keys[match.group(1)] = match.group(2)
    return keys


def extract_strings_from_bytes(data: bytes) -> str:
    try:
        result = subprocess.run(
            ["strings", "-"],
            input=data,
            capture_output=True,
            check=False,
        )
        return result.stdout.decode("utf-8", errors="replace")
    except FileNotFoundError:
        return data.decode("utf-8", errors="replace")


def collect_apk_text(apk_path: Path) -> str:
    chunks: list[str] = []
    with zipfile.ZipFile(apk_path) as archive:
        for name in archive.namelist():
            if not (
                name.endswith(".dex")
                or name.startswith("assets/")
                or name.endswith(".json")
                or name.endswith(".properties")
            ):
                continue
            try:
                chunks.append(extract_strings_from_bytes(archive.read(name)))
            except KeyError:
                continue
    return "\n".join(chunks)


def collect_jadx_text(apk_path: Path) -> str:
    jadx = subprocess.run(["which", "jadx"], capture_output=True, text=True)
    if jadx.returncode != 0:
        return ""

    with tempfile.TemporaryDirectory(prefix="enki-apk-") as tmp:
        out_dir = Path(tmp) / "src"
        result = subprocess.run(
            ["jadx", "-d", str(out_dir), str(apk_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return ""

        chunks: list[str] = []
        for path in out_dir.rglob("*"):
            if path.is_file() and path.suffix in {".java", ".json", ".xml", ".properties"}:
                try:
                    chunks.append(path.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    continue
        return "\n".join(chunks)


def find_keys_near_services(text: str) -> dict[str, set[str]]:
    """Map const symbol -> candidate keys appearing near service URL in text."""
    found: dict[str, set[str]] = {symbol: set() for symbol in SERVICE_MAP.values()}
    for service, symbol in SERVICE_MAP.items():
        for match in re.finditer(re.escape(service), text):
            start = max(0, match.start() - 400)
            end = min(len(text), match.end() + 400)
            window = text[start:end]
            for key_match in KEY_PATTERN.findall(window):
                found[symbol].add(key_match)
    return found


def rank_candidates(
    near_service: dict[str, set[str]],
    all_keys: set[str],
    const_keys: dict[str, str],
) -> dict[str, str | None]:
    """Pick best candidate per service."""
    resolved: dict[str, str | None] = {}
    known_values = {value for value in const_keys.values() if value}

    for symbol in SERVICE_MAP.values():
        candidates = set(near_service.get(symbol, set()))
        # Keys that match a known const value are strong signals for that slot
        for value in candidates & known_values:
            for name, const_value in const_keys.items():
                if const_value == value:
                    if name == symbol:
                        resolved[symbol] = value
                        break
            if symbol in resolved:
                continue

        if symbol in resolved:
            continue

        # Prefer candidates not already assigned to another known key
        fresh = [value for value in candidates if value not in known_values]
        if len(fresh) == 1:
            resolved[symbol] = fresh[0]
        elif len(candidates) == 1:
            resolved[symbol] = next(iter(candidates))
        else:
            resolved[symbol] = None
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="Path to Enki APK file")
    parser.add_argument("--jadx", action="store_true", help="Also decompile with jadx")
    args = parser.parse_args()

    if not args.apk.is_file():
        print(f"APK not found: {args.apk}", file=sys.stderr)
        return 1

    const_keys = read_const_keys()
    text = collect_apk_text(args.apk)
    if args.jadx:
        text += "\n" + collect_jadx_text(args.apk)

    all_keys = set(KEY_PATTERN.findall(text))
    near_service = find_keys_near_services(text)
    resolved = rank_candidates(near_service, all_keys, const_keys)

    print(f"APK: {args.apk}")
    print(f"Unique 32-char candidates: {len(all_keys)}\n")

    print("=== Validation (known keys in const.py) ===")
    for symbol, value in const_keys.items():
        if not value:
            continue
        status = "OK" if value in all_keys else "MISSING in APK"
        print(f"  {symbol}: {status}")

    print("\n=== Target keys (currently empty) ===")
    for symbol in sorted(MISSING_TARGETS):
        candidate = resolved.get(symbol)
        near = sorted(near_service.get(symbol, set()))
        print(f"  {symbol}:")
        if candidate:
            print(f"    -> {candidate}")
        elif near:
            print(f"    candidates near service URL: {', '.join(near)}")
        else:
            print("    -> not found (try --jadx or newer APK)")

    print("\n=== All service matches ===")
    for service, symbol in SERVICE_MAP.items():
        candidate = resolved.get(symbol)
        marker = " *" if symbol in MISSING_TARGETS and candidate else ""
        print(f"  {symbol}: {candidate or '(unresolved)'}{marker}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
