# Device profiles (referentiel)

Anonymized JSON sheets (capabilities + `possibleValues`) to document Enki models **without account or nodeId**. Source: referentiel API or community contributions.

| Device | Manufacturer | deviceId | HA status (fork) | Sheet |
|----------|-----------|----------|------------------|-------|
| ON/OFF relay | Equation | `63a053851a423d4a245a877c` | ✅ ON/OFF (consumption / timers: no) | [JSON](./63a053851a423d4a245a877c.json) |
| Water leak detector | Lexman | `651eada55b3a798ef6b6bc5c` | 🔬 beta — leak + battery OK remotely (#36, on-site leak test pending) | [JSON](./651eada55b3a798ef6b6bc5c.json) |
| Pilot wire controller | Equation | `63a054c81a423d4a245a877e` | ✅ stable v1.6.8+ — `select` pilot wire | [JSON](./63a054c81a423d4a245a877e.json) |
| Connected radiator | Noirot | `67a4b12bae1eca4709a45680` | ✅ stable v1.6.8+ — `climate` + detections | [JSON](./67a4b12bae1eca4709a45680.json) |

Profiles imported from [StephaneBranly/ha-enki#15](https://github.com/StephaneBranly/ha-enki/pull/15) (contribution [@zetiti10](https://github.com/zetiti10)). **Enki / Leroy Merlin scope only** — no third-party Zigbee (→ Zigbee2MQTT / ZHA).

To propose a new profile: opt-in telemetry in HA, [issue](https://github.com/cyrilcolinet/enki-integration-hass/issues/new?template=feature_request.yml), or PR with a JSON file in this folder.
