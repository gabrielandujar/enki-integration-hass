# Contributing

Thanks for contributing. For local setup, tests, and CI, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Before you code

1. Check [open issues](https://github.com/cyrilcolinet/enki-integration-hass/issues)
2. New Enki device: open a **feature request** with output from `scripts/discover_devices.py` (no password)
3. API context: [docs/API.md](docs/API.md)
4. Gateway keys (APK): [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) (`extract_gateway_keys.py`) · cover validation: [docs/BETA_VOLETS_KEY.md](docs/BETA_VOLETS_KEY.md)

## Quality bar

Before any PR:

```bash
ruff check .
ruff format .
pytest tests/unit -v
```

CI runs the same checks plus Hassfest and HACS.

## Code layout

- **`api/`** — auth, HTTP transport, Enki REST client
- **`domain/`** — models and capabilities (no Home Assistant imports)
- **`lib/`** — pure conversion and parsing, testable without HA
- **`platforms/`** — shared platform logic (not HA loader files)
- **`telemetry/`** — opt-in device profiles and legacy nudge
- **Root** — HA platform loaders (`fan.py`, `light.py`, `sensor.py`, `binary_sensor.py`, `climate.py`, `cover.py`, `number.py`, `select.py`, `switch.py`) + `config_flow.py` — full list in `__init__.py` → `PLATFORMS`

Public imports via each package `__init__.py` (`from enki.api import EnkiAPI`, etc.).

## Language

- **Python code** (comments, docstrings, symbol names): **English**
- **Markdown documentation** (`README.md`, `docs/`, `CONTRIBUTING.md`, …): **English**
- **Home Assistant UI strings** (notifications, config flow, `strings.json`, translations): **French and English** via HA translation files (`translations/fr.json`, `translations/en.json`)

## Pull requests

- One PR = one topic
- Conventional commits (`fix:`, `feat:`, `docs:`)
- Unit tests for changed logic
- No credentials in code or commits

Template: [.github/pull_request_template.md](.github/pull_request_template.md)

## Code of conduct

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
