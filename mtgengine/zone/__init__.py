"""Zone base class representing game areas in Magic: The Gathering."""

from typing import List

from mtgengine.card import Card


class Zone:
    """Base class for all game zones."""

    def __init__(self, name: str) -> None:
        """Initialize a Zone with an empty list of cards.

        Args:
            name: The name of the zone.
        """
        self.name = name
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
