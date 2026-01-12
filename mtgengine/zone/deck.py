"""Deck class representing an ordered collection of cards."""

import random

from mtgengine.card import Card
from mtgengine.zone import Zone


class Deck(Zone):
    """Represents a player's deck, maintaining cards in insertion order."""

    def __init__(self) -> None:
        """Initialize an empty Deck."""
        super().__init__("Deck")

    def shuffle(self, rng: random.Random) -> None:
        """Shuffle the deck in-place using the provided RNG.

        Args:
            rng: A random.Random instance (or any object with shuffle method).
        """
        rng.shuffle(self.cards)

    def draw(self, n: int = 1) -> list[Card]:
        """Draw n cards from the top of the deck (removes them).

        Args:
            n: Number of cards to draw. Defaults to 1.

        Returns:
            A list of Card objects drawn from the top of the deck.

        Note:
            Assumes the deck has at least n cards.
        """
        return [self.cards.pop() for _ in range(n)]
