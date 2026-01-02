"""Card class representing a Magic: The Gathering card."""

from mtgengine.mana_cost import ManaCost


class Card:
    """Represents a Magic: The Gathering card."""

    def __init__(self, name: str, mana_cost: ManaCost | None = None) -> None:
        """Initialize a Card.

        Args:
            name: The name of the card.
            mana_cost: The mana cost of the card. Defaults to zero cost.
        """
        self.name = name
        self.mana_cost = mana_cost or ManaCost()
