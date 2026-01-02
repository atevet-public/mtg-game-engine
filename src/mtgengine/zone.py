"""Zone classes representing different game areas in Magic: The Gathering."""

from typing import List
from src.mtgengine.card import Card


class Zone:
    """Base class for all game zones."""

    def __init__(self) -> None:
        """Initialize a Zone with an empty list of cards."""
        self.cards: List[Card] = []

    def add_card(self, card: Card) -> None:
        """
        Add a card to the zone.

        Args:
            card: The card to add.
        """
        self.cards.append(card)

    def remove_card(self, card: Card) -> None:
        """
        Remove a card from the zone.

        Args:
            card: The card to remove.
        """
        if card in self.cards:
            self.cards.remove(card)

    def get_cards(self) -> List[Card]:
        """
        Get all cards in the zone.

        Returns:
            A list of all cards in the zone.
        """
        return self.cards.copy()


class Battlefield(Zone):
    """Represents the battlefield zone."""

    def __init__(self) -> None:
        """Initialize the Battlefield zone."""
        super().__init__()
        self.name = "Battlefield"


class Graveyard(Zone):
    """Represents the graveyard zone."""

    def __init__(self) -> None:
        """Initialize the Graveyard zone."""
        super().__init__()
        self.name = "Graveyard"


class Exile(Zone):
    """Represents the exile zone."""

    def __init__(self) -> None:
        """Initialize the Exile zone."""
        super().__init__()
        self.name = "Exile"


class Hand(Zone):
    """Represents a player's hand zone."""

    def __init__(self) -> None:
        """Initialize the Hand zone."""
        super().__init__()
        self.name = "Hand"


class Stack(Zone):
    """Represents the stack zone."""

    def __init__(self) -> None:
        """Initialize the Stack zone."""
        super().__init__()
        self.name = "Stack"
