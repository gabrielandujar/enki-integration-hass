"""Unit tests for fan blade rotation / season mapping."""

from __future__ import annotations

from enki.const import DIRECTION_FORWARD, DIRECTION_REVERSE
from enki.helpers import direction_to_enki_rotation, enki_rotation_to_direction


def test_enki_rotation_to_direction_summer_winter() -> None:
    assert enki_rotation_to_direction("SUMMER") == DIRECTION_FORWARD
    assert enki_rotation_to_direction("WINTER") == DIRECTION_REVERSE
    assert enki_rotation_to_direction("summer") == DIRECTION_FORWARD


def test_enki_rotation_to_direction_clockwise_aliases() -> None:
    assert enki_rotation_to_direction("COUNTER_CLOCKWISE") == DIRECTION_FORWARD
    assert enki_rotation_to_direction("CLOCKWISE") == DIRECTION_REVERSE
    assert enki_rotation_to_direction("CCW") == DIRECTION_FORWARD
    assert enki_rotation_to_direction("CW") == DIRECTION_REVERSE


def test_enki_rotation_to_direction_from_state_dict() -> None:
    assert enki_rotation_to_direction({"rotation": "WINTER"}) == DIRECTION_REVERSE
    assert enki_rotation_to_direction({"bladeDirection": "SUMMER"}) == DIRECTION_FORWARD


def test_direction_to_enki_rotation_round_trip() -> None:
    assert direction_to_enki_rotation(DIRECTION_FORWARD) == "SUMMER"
    assert direction_to_enki_rotation(DIRECTION_REVERSE) == "WINTER"
    assert enki_rotation_to_direction(direction_to_enki_rotation(DIRECTION_FORWARD)) == (
        DIRECTION_FORWARD
    )
