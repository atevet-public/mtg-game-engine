"""Deck class representing an ordered collection of cards."""

from src.mtgengine.zone import Zone


class Deck(Zone):
    """Represents a player's deck, maintaining cards in insertion order."""

    def __init__(self) -> None:
        """Initialize an empty Deck."""
        super().__init__()
