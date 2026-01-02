"""Tests for Player class."""

import pytest
from src.mtgengine.player import Player


class TestPlayer:
    """Test suite for the Player class."""

    def test_player_initialization_with_defaults(self) -> None:
        """Test Player initialization with default life total."""
        player = Player("Alice")
        assert player.name == "Alice"
        assert player.life_total == 20

    def test_player_initialization_with_custom_life_total(self) -> None:
        """Test Player initialization with custom life total."""
        player = Player("Bob", 30)
        assert player.name == "Bob"
        assert player.life_total == 30

    def test_player_with_zero_life_total(self) -> None:
        """Test Player with zero life total."""
        player = Player("Charlie", 0)
        assert player.name == "Charlie"
        assert player.life_total == 0

    def test_player_with_high_life_total(self) -> None:
        """Test Player with high life total."""
        player = Player("Dave", 1000)
        assert player.name == "Dave"
        assert player.life_total == 1000

    def test_player_name_property(self) -> None:
        """Test accessing player name property."""
        player = Player("Eve")
        assert player.name == "Eve"

    def test_player_life_total_property(self) -> None:
        """Test accessing player life total property."""
        player = Player("Frank", 15)
        assert player.life_total == 15
