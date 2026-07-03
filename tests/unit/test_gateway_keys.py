"""Unit tests for mobile-config gateway key parsing."""

from __future__ import annotations

from enki.api.gateway_keys import GatewayKeyStore, parse_mobile_config_keys


def test_parse_mobile_config_service_api_key_pairs() -> None:
    payload = {
        "gateways": [
            {
                "service": "api-enki-heating-prod",
                "apiKey": "a" * 32,
            },
            {
                "microService": "api-enki-rolling-prod",
                "gatewayApiKey": "b" * 32,
            },
        ]
    }
    mapped = parse_mobile_config_keys(payload)
    assert mapped["ENKI_HEATING_API_KEY"] == "a" * 32
    assert mapped["ENKI_ACCESS_MOTORIZATION_API_KEY"] == "b" * 32


def test_parse_mobile_config_slug_as_dict_key() -> None:
    payload = {
        "api-enki-water-leak-detector-prod": "c" * 32,
    }
    mapped = parse_mobile_config_keys(payload)
    assert mapped["ENKI_WATER_SENSOR_API_KEY"] == "c" * 32


def test_parse_mobile_config_legacy_water_sensor_slug() -> None:
    payload = {
        "services": [
            {
                "slug": "api-enki-water-sensor-prod",
                "apiKey": "d" * 32,
            }
        ]
    }
    mapped = parse_mobile_config_keys(payload)
    assert mapped["ENKI_WATER_SENSOR_API_KEY"] == "d" * 32


def test_gateway_key_store_applies_to_const(monkeypatch) -> None:
    import enki.const as const_module

    monkeypatch.setattr(const_module, "ENKI_HEATING_API_KEY", "")
    store = GatewayKeyStore()
    payload = {"api-enki-heating-prod": "e" * 32}
    applied = store.apply_mobile_config(payload)
    assert applied["ENKI_HEATING_API_KEY"] == "e" * 32
    assert const_module.ENKI_HEATING_API_KEY == "e" * 32
    assert store.get_transport_key("heating") == "e" * 32


def test_gateway_key_store_does_not_override_filled_const(monkeypatch) -> None:
    import enki.const as const_module

    monkeypatch.setattr(const_module, "ENKI_HOME_API_KEY", "existing-home-key-0123456789012")
    store = GatewayKeyStore()
    payload = {"api-enki-home-prod": "f" * 32}
    store.apply_mobile_config(payload)
    assert const_module.ENKI_HOME_API_KEY == "existing-home-key-0123456789012"
