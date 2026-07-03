#!/usr/bin/env python3
"""Fetch Enki gateway API keys via mobile-config (same source as the app).

The Enki 2.25.1 APK embeds only ENKI_HOME_API_KEY in DEX; other keys are
loaded at runtime from api-enki-mobile-config-prod (endpoint config/app/).

Usage:
    python scripts/fetch_gateway_keys.py your@email.com 'your-password'

Prints raw JSON from mobile-config and any 32-char key candidates found.
Use the output to update custom_components/enki/const.py.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components"))

from enki.api.auth import EnkiAuthSession  # noqa: E402
from enki.const import ENKI_BASE_URL, ENKI_HOME_API_KEY  # noqa: E402

KEY_PATTERN = re.compile(r"[A-Za-z0-9]{32}")
CONFIG_PATH = "/api-enki-mobile-config-prod/v1/config/app/"


async def fetch_config(username: str, password: str) -> dict:
    import aiohttp

    auth = EnkiAuthSession(username, password)
    async with aiohttp.ClientSession() as session:
        await auth.connect(session)
        url = f"{ENKI_BASE_URL}{CONFIG_PATH}"
        headers = auth.auth_headers(
            {"X-Gateway-APIKey": ENKI_HOME_API_KEY},
        )
        async with session.get(url, headers=headers) as response:
            body = await response.text()
            if response.status != 200:
                raise RuntimeError(
                    f"GET {CONFIG_PATH} failed: HTTP {response.status}\n{body[:500]}"
                )
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Non-JSON response from mobile-config: {exc}\n{body[:500]}"
                ) from exc
            if not isinstance(payload, dict):
                raise RuntimeError(f"Unexpected mobile-config payload type: {type(payload)!r}")
            return payload


def collect_keys(obj: object, found: set[str]) -> None:
    if isinstance(obj, str) and KEY_PATTERN.fullmatch(obj):
        found.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            collect_keys(value, found)
    elif isinstance(obj, list):
        for item in obj:
            collect_keys(item, found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument("password")
    args = parser.parse_args()

    payload = asyncio.run(fetch_config(args.username, args.password))
    print(json.dumps(payload, indent=2, sort_keys=True))

    keys: set[str] = set()
    collect_keys(payload, keys)
    if keys:
        print("\n=== 32-char key candidates ===", file=sys.stderr)
        for key in sorted(keys):
            print(key, file=sys.stderr)
    else:
        print("\n(no 32-char keys in JSON — inspect structure above)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
