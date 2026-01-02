"""Tests for Player class."""

import pytest

from mtgengine.player import Player


class TestPlayer:
    """Test suite for the Player class."""

    @pytest.mark.parametrize(
        "name,life_total",
        [
            ("Alice", 20),
            ("Bob", 40),
            ("Charlie", 0),
        ],
    )
    def test_player_initialization(
        self,
        name: str,
        life_total: int,
    ) -> None:
        """Test Player initialization with various parameters."""
        player = Player(name, life_total)
        assert player.name == name
        assert player.life_total == life_total
