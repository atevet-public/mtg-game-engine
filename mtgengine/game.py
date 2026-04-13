"""Game class representing a Magic: The Gathering game."""

import random

from mtgengine.player import Player
from mtgengine.zone.stack import Stack


class Game:
    """Represents a Magic: The Gathering game."""

    def __init__(self, players: list[Player]) -> None:
        """Initialize a Game with one or more players and a shared stack.

        Args:
            players: List of players in the game (must have at least one).

        Raises:
            ValueError: If players list is empty.
        """
        if not players:
            raise ValueError("A game must have at least one player")
        self.players = players
        self.stack = Stack()
        self.current_player_index: int | None = None
        self.turn_number: int = 0
        self.active_player: Player | None = None
        self.priority_player: Player | None = None

    def start_game(self, rng: random.Random | None = None) -> None:
        """Start the game: shuffle decks, deal 7 cards to each player, and select first player.

        Args:
            rng: A random.Random instance for RNG operations. If None, a new Random is created.
        """
        rng = rng or random.Random()

        # Shuffle each player's deck
        for player in self.players:
            player.deck.shuffle(rng)

        # Deal 7 cards to each player
        for player in self.players:
            player.draw_from_deck(7)

        # Select first player randomly
        self.current_player_index = rng.randrange(len(self.players))
        self.active_player = self.players[self.current_player_index]

    def check_state_based_actions(self) -> bool:
        """Check and apply state-based actions. Returns True if any were applied."""
        return False  # Implemented in Phase 4

    def pass_priority(self, player: Player) -> None:
        """Pass priority from the given player to the next."""
        pass

    def advance_to_next_step(self) -> None:
        """Advance the game to the next step/phase."""
        pass
