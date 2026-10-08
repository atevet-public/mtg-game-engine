"""Zone base class representing game areas in Magic: The Gathering."""

from copy import deepcopy

from mtgengine.card import Card


class Zone:
    """Base class for all game zones."""

    def __init__(self, name: str) -> None:
        """Initialize a Zone with an empty list of cards.

        Args:
            name: The name of the zone.
        """
        self.name = name
        self.cards: list[Card] = []

    def add_card(self, card: Card) -> None:
        """
        Add a card to the zone.

        Args:
            card: The card to add.
        """
        self.add_cards(card, 1)

    def add_cards(self, card: Card, quantity: int) -> None:
        """Add a card to the zone the given number of times.

        The supplied card is added first; each additional copy is an independent
        copy so that copies do not share mutable state.

        Args:
            card: The card to add.
            quantity: How many copies to add.
        """
        for index in range(quantity):
            self.cards.append(card if index == 0 else deepcopy(card))

    def remove_card(self, card: Card) -> None:
        """
        Remove a card from the zone.

        Args:
            card: The card to remove.
        """
        if card in self.cards:
            self.cards.remove(card)

    def get_cards(self) -> list[Card]:
        """
        Get all cards in the zone.

        Returns:
            A list of all cards in the zone.
        """
        return self.cards.copy()
