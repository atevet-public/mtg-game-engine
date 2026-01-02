"""Tests for Game class."""

from src.mtgengine.game import Game


class TestGame:
    """Test suite for the Game class."""

    def test_game_initialization(self) -> None:
        """Test Game initialization."""
        game = Game()
        assert game is not None
        assert isinstance(game, Game)
