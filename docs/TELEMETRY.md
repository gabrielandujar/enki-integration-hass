# Device telemetry (opt-in)

Optional telemetry helps map unknown Enki hardware and improve test fixtures. It is **disabled by default**.

## What users enable

In **Settings → Devices & services → Enki → Configure**, enable:

> Share anonymized device metadata (creates GitHub issues to improve support)

On each poll, new device profiles (unique capability fingerprint) are sent once.

## What is sent

- Device type (referentiel + BFF)
- Manufacturer / model / firmware (when available)
- Capabilities and `possibleValues` schema
- Integration and Home Assistant version

**Never sent:** email, password, tokens, home/node IDs, room names, device labels.

## What is created

A GitHub issue labeled `device-telemetry` is opened automatically via `repository_dispatch`. Duplicates are skipped (fingerprint).

## Maintainer setup

1. Create a **fine-grained PAT** on GitHub with **Actions: Read and write** on this repository only.
2. Set `TELEMETRY_DISPATCH_TOKEN` in `custom_components/enki/const.py` before release (or via a private fork overlay).
3. Ensure workflow `.github/workflows/telemetry-report.yml` is on `main`.

Without a dispatch token, opt-in users see no error — reporting is skipped (`DEBUG` log only).

## Manual export (no opt-in)

```bash
python3 scripts/discover_devices.py <email> <password> --export
```

Writes anonymized JSON to stdout for issue templates.

## Diagnostics (local)

Home Assistant **Download diagnostics** on the config entry exports the same anonymized profiles locally — useful for support without enabling GitHub telemetry.
