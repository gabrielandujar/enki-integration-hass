"""Unit tests for fan speed percentage mapping."""

from __future__ import annotations

from enki.helpers import percentage_to_speed, speed_to_percentage


def test_speed_to_percentage_levels() -> None:
    assert speed_to_percentage(0) == 0
    assert speed_to_percentage(1) == 0
    assert speed_to_percentage(6) == 100


def test_percentage_round_trip() -> None:
    # Speed 1 maps to 0 % in HA (minimum non-off step); round-trip from 2 upward.
    for speed in range(2, 7):
        percentage = speed_to_percentage(speed)
        restored = percentage_to_speed(percentage)
        assert restored == speed
