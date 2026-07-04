# Roadmap (detailed view)

Short version: [README](../README.md) · detailed view below.

| | |
|---|---|
| **Latest GitHub release** | [releases](https://github.com/cyrilcolinet/enki-integration-hass/releases/latest) |
| **Repository `manifest.json`** | 1.6.5 |

## Status by device

| Status | Device | Features |
|--------|----------|-------------------|
| ✅ Supported | Inspire fans (Siroco+, Cadix, …) | fan, LED kit light, speed, direction, modes (per referentiel) |
| ✅ Supported | Enki lights (Eglo, Lexman, …) | ON/OFF, brightness, tunable white, RGB (HS) if `change_hue` + `change_saturation` |
| ✅ Supported | Outlets / switches (Edisio, Equation, …) | ON/OFF via `switch-electrical-power` |
| ✅ Supported | Envertech-Lexman solar panels | production (W) via BFF dashboard |
| ✅ Supported | Motion / contact / vibration sensors (Lexman, …) | `binary_sensor` |
| ✅ Supported | Enki thermometers (Sedea, …) | temperature, humidity, battery |
| ✅ Supported | Lexman sirens | `switch` ON/OFF |
| ✅ Supported | Equation ON/OFF relay | ON/OFF (like Edisio outlets) |
| 🔬 Beta | Roller shutters (Evology, Nodon, …) | `cover` “Shutter (beta)” if active in the app; `ENKI_ACCESS_MOTORIZATION_API_KEY` (APK 2.25.1); limited real-world testing |
| 🔬 Beta | Lexman water leak detector (v1.5.0+) | leak `binary_sensor` + battery `sensor`; `ENKI_WATER_SENSOR_API_KEY` and `ENKI_BATTERY_HEALTH_API_KEY` (APK 2.25.1) |
| 🔬 Beta | Equation pilot wire (v1.5.0+) | `select` entity (comfort / eco / frost protection modes); `ENKI_HEATING_API_KEY` (APK 2.25.1) |
| 🔬 Beta | Noirot radiator (v1.5.0+) | `climate` + window / presence detection; `ENKI_HEATING_API_KEY` (APK 2.25.1) |
| 🔜 Soon | ACOVA ARLAN radiators | manufacturer allowlist OK, no test hardware |
| 🔬 Beta | Enki scenarios (“Open living room”, …) | `button` (v1.6.0+) |
| ⏳ Not planned | Enki alarm | no API identified |
| ✅ Prerequisite OK | Default HACS store | CI HACS + Hassfest green, releases published — [PR to `hacs/default`](HACS.md#default-hacs-store) |

**Out of scope:** third-party Zigbee on the hub (Sonoff, Tuya, Aqara, IKEA, …) → [Zigbee2MQTT](https://www.zigbee2mqtt.io/) or ZHA. Only **Enki / Leroy Merlin** brands in [`lib/enki_scope.py`](../custom_components/enki/lib/enki_scope.py) are imported.
