"""Game class representing a Magic: The Gathering game."""

import random

from mtgengine.player import Player
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.stack import Stack


class Game:
    """Represents a Magic: The Gathering game."""

    def __init__(self, players: list[Player]) -> None:
        """Initialize a Game with one or more players and shared game zones.

        The battlefield is modeled as a shared zone. Deck, hand, graveyard, and
        exile remain player-owned zones in the current model. The stack is shared.
        Each player keeps an intentional ``player.game`` back-reference for
        event handlers that need shared game context.

        Args:
            players: List of players in the game (must have at least one).

        Raises:
            ValueError: If players list is empty.
        """
        if not players:
            raise ValueError("A game must have at least one player")
        self.players = players
        self.battlefield = Battlefield()
        self.stack = Stack()
        self.current_player_index: int | None = None
        self.turn_number = 1
        for player in self.players:
            player.game = self

    def start_game(self, rng: random.Random | None = None) -> None:
        """Start the game: shuffle decks, deal 7 cards to each player, and select first player.

        Args:
            rng: A random.Random instance for RNG operations. If None, a new Random is created.
        """
        rng = rng or random.Random()

        # Shuffle each player's deck
        for player in self.players:
            player.deck.shuffle(rng)

        self.current_player_index = 0
        self.turn_number = 1

        # Deal 7 cards to each player
        for player in self.players:
            player.draw_from_deck(7)
