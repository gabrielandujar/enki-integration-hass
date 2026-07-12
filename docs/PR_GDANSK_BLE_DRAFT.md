# GDANSK BLE support for `light` entities

## Summary

This change adds a local BLE control path for the GDANSK ceiling panel (`referentiel_model = ZBEK-29`) while preserving the existing cloud behavior for every other Enki light.

The goal is to keep the same Home Assistant `light` entity and make these features work on the GDANSK panel:

- `turn_on`
- `turn_off`
- brightness
- color temperature
- HS color

## Why this is needed

For this specific model, the current cloud lighting flow is not reliable:

- the device is visible in Enki
- the generic light entity is created correctly
- but `check-light-state` returns `HTTP 400` for this panel
- the mobile app still controls it successfully because it uses local BLE, not the cloud lighting endpoint

So the issue is not entity modeling in Home Assistant. The issue is that this model does not have a usable cloud `check-light-state` path for normal light control.

## What this change does

- Detect GDANSK explicitly from stable discovery metadata: `referentiel_model == "ZBEK-29"`.
- Add a dedicated local backend in `custom_components/enki/api/ble_gdansk.py`.
- Route GDANSK light state reads through BLE instead of the failing cloud `check-light-state` endpoint.
- Route GDANSK `light` commands through BLE instead of the cloud lighting API.
- Keep the existing cloud implementation unchanged for all other Enki lights.

## BLE protocol used

The implementation is intentionally model-specific and follows the validated GDANSK protocol:

- Service: `0000a100-1115-1000-0001-617573746f6d`
- Write: `0000a101-1115-1000-0001-617573746f6d`
- Notify: `0000a102-1115-1000-0001-617573746f6d`

### Handshake

- `0x2001`

### State queries

- `0x1002` power
- `0x1102` brightness
- `0x130D` mode / color
- `0x1202` color temperature

### Commands

- `0x1001` power
- `0x1101` brightness
- `0x1201` color temperature
- `0x1307` HS color

### Parsed notifications

- `0x1003`
- `0x1103`
- `0x1203`
- `0x130E`
- `0x1309`

## Home Assistant behavior

The GDANSK panel remains a standard `light` entity in Home Assistant. The entity now updates its cached state from BLE-compatible fields:

- `power`
- `light_power`
- `brightness`
- `colorTemperature`
- `hue`
- `saturation`
- `colorMode`

This allows the entity to expose and reflect:

- on/off
- brightness
- color temperature
- HS color mode

## Scope

This PR does **not** attempt to introduce a generic BLE framework for Enki devices.

It intentionally adds a focused support path for:

- GDANSK
- `ZBEK-29`
- local BLE control through the existing `light` entity

## Validation

- Unit tests added for BLE frame building and notification parsing
- Unit tests added for GDANSK routing
- Full unit test suite passes locally

