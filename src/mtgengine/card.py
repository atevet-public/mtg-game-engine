"""Card class representing a Magic: The Gathering card."""


class Card:
    """Represents a Magic: The Gathering card."""

    def __init__(self, name: str, mana_cost: int, card_type: str) -> None:
        """
        Initialize a Card.

        Args:
            name: The name of the card.
            mana_cost: The mana cost of the card.
            card_type: The type of the card (e.g., "Creature", "Sorcery").
        """
        self.name = name
        self.mana_cost = mana_cost
        self.card_type = card_type
