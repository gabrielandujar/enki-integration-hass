# Supported devices and features

Detail by device type and Home Assistant entities created. The integration detects devices via API **capabilities** (like the mobile app), not model names alone.

| | |
|---|---|
| **Latest GitHub release** | [releases](https://github.com/cyrilcolinet/enki-integration-hass/releases/latest) |
| **Repository `manifest.json`** | 1.6.5 |

Summary: [ROADMAP.md](ROADMAP.md)

## Scope

This integration covers **only the Enki / Leroy Merlin ecosystem**: Lexman, Equation, Inspire, Noirot, Edisio, Eglo, Sedea, Evology, Nodon, ACOVA, Envertech, etc. (exact list: [`lib/enki_scope.py`](../custom_components/enki/lib/enki_scope.py)).

**Important:** many of these devices use **Zigbee radio** via the Enki hub — that is expected and in scope. However, any **third-party Zigbee** on the hub (Sonoff, Tuya, Aqara, IKEA, …) or any node **without a known Enki manufacturer** is **skipped** at discovery: integrate them via **Zigbee2MQTT** or **ZHA**, not this repo.

## Inspire ceiling fans (Siroco+, Aruba+, Cadix, Radix, …)

**HA entities:** `fan` + `light` (LED kit)

| Function | Detail |
|----------|--------|
| On / off | Speed 0 or motor power cut |
| Speed | Up to 6 levels (HA percentage mapping; max from referentiel) |
| Rotation direction | Summer / winter if `change_fan_rotation_direction` (API `CLOCKWISE` / `COUNTERCLOCKWISE`) |
| Modes | HA presets from referentiel: `manual`, `breeze`, and per model `ventilation`, `boost`, `auto`, `sleep` (UI label “Night”) |

Fan and light kit are **independent**: turning one on does not turn the other on.

## Enki lights (Eglo, Lexman, …)

**HA entity:** `light`

| Function | Detail |
|----------|--------|
| On / off | ON / OFF |
| Brightness | If `change_brightness` or `change_light_state` |
| Tunable white | Color temperature (`colorTemperature`, e.g. `T3500K`) when advertised |
| RGB color | HS mode if `change_hue` + `change_saturation` (since manifest **1.4.0**) |

## Outlets, relays, and switches (Edisio, Equation, …)

**HA entity:** `light` ON/OFF (API `switch-electrical-power`, not lighting API)

| Model / type | Status |
|---------------|--------|
| Edisio outlets | ✅ ON/OFF, ✅ instant consumption (W) |
| Equation ON/OFF relay ([profile](./devices/63a053851a423d4a245a877c.json)) | ✅ ON/OFF, ✅ instant consumption (W) |

Multi-circuit nodes may create **one entity per circuit** (BFF endpoint). Timers (`switch_electrical_power_in`, …): not exposed yet.

## Enki scenarios (v1.6.0+)

**HA entities:** `button` (one button per cloud scenario)

| Function | Detail |
|----------|--------|
| List | `GET /api-enki-scenario-prod/v1/scenarios?homeId=…` |
| Run | `POST …/scenarios/{id}/activate` |

Scenarios refresh on each coordinator poll. They appear under the virtual device **Enki scenarios**.

## Solar panels (Envertech-Lexman)

**HA entity:** `sensor` (production W)

| Function | Detail |
|----------|--------|
| Instant production | Value from BFF dashboard (`description.value`) |

## Enki sensors (Lexman, Sedea, …)

Micro-services aligned with [StephaneBranly/ha-enki](https://github.com/StephaneBranly/ha-enki) (gateway keys already in `const.py`).

### Motion / contact / vibration

**HA entities:** `binary_sensor`

| API capability | Entity |
|----------------|--------|
| `check_motion_detection` / `check_motion_detector_state` | Motion |
| `check_contact_sensor_state` | Contact (open / closed) |
| `check_vibration_detection` | Vibration |

### Temperature / humidity / battery

**HA entities:** `sensor`

| API capability | Entity |
|----------------|--------|
| `check_current_temperature` | Temperature (°C) — except thermostats (temperature on `climate`) |
| `check_current_humidity` | Humidity (%) |
| `check_battery_health` | Battery (%, Enki mapping) |

**Sedea** thermometers (display): temperature, humidity, battery.

### Lexman siren

**HA entity:** `switch` (ON/OFF via `switch_siren_status`)

### Contact sensor settings

**HA entities:** `switch` (detection enable), `number` (vibration sensitivity 1–5)

### Water leak (Lexman) — beta (v1.5.0+)

**HA entities:** `binary_sensor` (leak), `sensor` (battery)

**Profile:** [651eada55b3a798ef6b6bc5c.json](./devices/651eada55b3a798ef6b6bc5c.json)

| Capability | Service | Current status |
|------------|---------|---------------|
| `check_battery_health` | `battery-health` | ✅ APK 2.25.1 key |
| `check_water_sensor_state` | `water-leak-detector` | ✅ APK 2.25.1 key |

## Heating — beta (v1.5.0+)

| Model | HA entities | Profile |
|--------|------------|--------|
| Equation pilot wire | `select` (COMFORT, ECO, FROST_PROTECTION, OFF, …) | [63a054c81a423d4a245a877e.json](./devices/63a054c81a423d4a245a877e.json) |
| Noirot radiator | `climate`, `binary_sensor` (window, presence), `switch` (detection modes) | [67a4b12bae1eca4709a45680.json](./devices/67a4b12bae1eca4709a45680.json) |

**API keys:** from Enki APK 2.25.1 (`ENKI_HEATING_API_KEY`, `ENKI_WATER_SENSOR_API_KEY`). Update: [DEVELOPMENT.md](DEVELOPMENT.md) · API detail: [API.md](API.md#heating-and-water-sensors-manifest--150).

JSON catalogue: [docs/devices/README.md](./devices/README.md)

## Roller shutters — beta (Evology, Nodon, …)

**HA entity:** `cover` “Shutter (beta)”

| Function | Detail |
|----------|--------|
| Open / close | HA cover commands |
| Position | 0–100 % via `change-shutter-position` |

**Current state:** `ENKI_ACCESS_MOTORIZATION_API_KEY` included (APK 2.25.1). Micro-service: `api-enki-rolling-prod` (not `access-and-motorizations`). **“Shutter (beta)”** entity if the shutter is active in the Enki app.

Contributor network feedback: [BETA_VOLETS_KEY.md](BETA_VOLETS_KEY.md).

### For testers (covers)

1. Update the Enki integration (**v1.5.0+**) via HACS, then restart Home Assistant.
2. Check the **“Shutter (beta)”** entity under Enki.
3. Test open / close / position vs the Enki mobile app.
4. Report results (model, HA version, integration version, `enki` log excerpt if it fails).

## Cross-cutting features

- **OAuth auth** — Keycloak refresh token; HA notification on invalid credentials
- **Opt-in telemetry** — notification for unknown profiles, pre-filled GitHub link (nothing sent without a click)
- **Operational notifications** — login failure, gateway key 403, cloud unreachable ([API.md](API.md#operational-notifications))
- **Diagnostics** — anonymized JSON export from Enki UI

## In progress / not supported

| Status | Topic |
|--------|--------|
| Beta | Covers, heating, water leak, scenarios — APK 2.25.1 keys, feedback welcome |
| Soon | ACOVA ARLAN radiators (same heating API if capabilities match) |
| Not planned | Enki alarm (no API identified) |
| Out of scope | Enki hub, pairing, Leroy Merlin account → [Enki support](https://support.enki-home.com/) |

API documentation: [API.md](API.md)
