"""Battlefield zone representing the battlefield in Magic: The Gathering."""

from mtgengine.card import Card
from mtgengine.zone import Zone


class Battlefield(Zone):
    """Represents the battlefield zone."""

    def __init__(self) -> None:
        """Initialize the Battlefield zone."""
        super().__init__("Battlefield")

    def add_card(self, card: Card) -> None:
        """Add a card to the battlefield with owner metadata validation."""
        if type(card.owner_index) is not int or card.owner_index < 0:
            raise ValueError("Battlefield cards must have owner_index set to a non-negative int.")
        super().add_card(card)
