"""Tests for PlayerSpecification."""

import pytest

from mtgengine.player_specification import PlayerSpecification


def test_player_specification_is_immutable() -> None:
    specification = PlayerSpecification("Alice", "60 Forest")
    with pytest.raises(AttributeError):
        specification.name = "Bob"  # type: ignore[misc]
