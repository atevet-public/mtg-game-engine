"""Game class representing a Magic: The Gathering game."""

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
