#!/usr/bin/env python3
"""Discover Enki devices and print API metadata (development helper).

Usage:
    python3 scripts/discover_devices.py <email> <password>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components"))

from enki.api import EnkiAPI  # noqa: E402


async def main(username: str, password: str) -> None:
    api = EnkiAPI(username, password)
    await api.async_connect()
    devices = await api.async_get_devices()
    for device in devices:
        print(
            json.dumps(
                {
                    "name": device.device_name,
                    "type": device.device_type,
                    "nodeId": device.node_id,
                    "homeId": device.home_id,
                    "capabilities": device.capabilities,
                    "state": device.state,
                    "enabled": device.is_enabled,
                },
                indent=2,
            )
        )
        print("---")
    await api.async_close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <email> <password>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
