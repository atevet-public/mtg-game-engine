"""Tests for Game class."""

import random

import pytest

from mtgengine.card import Card
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

    def test_start_game_deals_hands_and_sets_current_player(self) -> None:
        """Test that start_game deals 7 cards and sets current player."""
        # Create players with 20 cards each
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)

        # Populate their decks with cards
        for i in range(20):
            card = Card(f"Card {i}", card_type="Creature")
            player1.deck.add_card(card)
            card = Card(f"Card {i}", card_type="Creature")
            player2.deck.add_card(card)

        game = Game([player1, player2])

        # Use a seeded RNG for deterministic testing
        rng = random.Random(42)
        game.start_game(rng=rng)

        # Each player should have 7 cards in hand
        assert len(player1.hand.get_cards()) == 7
        assert len(player2.hand.get_cards()) == 7

        # Each player should have 13 cards left in deck (20 - 7)
        assert len(player1.deck.get_cards()) == 13
        assert len(player2.deck.get_cards()) == 13

        # Current player should be set to a valid index
        assert game.current_player_index is not None
        assert 0 <= game.current_player_index < len(game.players)

    def test_start_game_without_rng_parameter(self) -> None:
        """Test that start_game works without an explicit RNG parameter."""
        # Create players with 20 cards each
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)

        # Populate their decks with cards
        for i in range(20):
            card = Card(f"Card {i}", card_type="Creature")
            player1.deck.add_card(card)
            card = Card(f"Card {i}", card_type="Creature")
            player2.deck.add_card(card)

        game = Game([player1, player2])

        # Call start_game without rng parameter (uses default)
        game.start_game()

        # Each player should have 7 cards in hand
        assert len(player1.hand.get_cards()) == 7
        assert len(player2.hand.get_cards()) == 7

        # Current player should be set to a valid index
        assert game.current_player_index is not None
        assert 0 <= game.current_player_index < len(game.players)
