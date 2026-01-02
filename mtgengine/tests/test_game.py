"""Tests for Game class."""

import pytest

from mtgengine.game import Game
from mtgengine.player import Player
from mtgengine.zone.stack import Stack


class TestGame:
    """Test suite for the Game class."""

    def test_game_initialization(self) -> None:
        """Test that a game initializes with players and a stack."""
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)
        game = Game([player1, player2])
        assert game.players == [player1, player2]
        assert isinstance(game.stack, Stack)

    def test_game_single_player(self) -> None:
        """Test that a game can be created with a single player."""
        player = Player("Solo", 20)
        game = Game([player])
        assert len(game.players) == 1
        assert game.players[0] is player

    def test_game_requires_at_least_one_player(self) -> None:
        """Test that game raises ValueError with no players."""
        with pytest.raises(ValueError, match="at least one player"):
            Game([])
