"""Tests for PlayerSpecification."""

import pytest

from mtgengine.player_specification import PlayerSpecification


def test_player_specification_is_immutable() -> None:
    specification = PlayerSpecification("Alice", "60 Forest")
    with pytest.raises(AttributeError):
        specification.name = "Bob"  # type: ignore[misc]


def test_player_specification_has_default_and_configurable_starting_life() -> None:
    assert PlayerSpecification("Alice", "60 Forest").starting_life == 20
    assert PlayerSpecification("Bob", "60 Island", starting_life=30).starting_life == 30
