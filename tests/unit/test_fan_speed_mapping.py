"""Unit tests for fan speed percentage mapping."""

from __future__ import annotations

from enki.helpers import percentage_to_speed, speed_to_percentage


def test_speed_to_percentage_levels() -> None:
    assert speed_to_percentage(0) == 0
    assert speed_to_percentage(1) == 17
    assert speed_to_percentage(3) == 50
    assert speed_to_percentage(6) == 100


def test_percentage_round_trip() -> None:
    for speed in range(1, 7):
        percentage = speed_to_percentage(speed)
        restored = percentage_to_speed(percentage)
        assert restored == speed


def test_percentage_zero_is_off() -> None:
    assert percentage_to_speed(0) == 0
