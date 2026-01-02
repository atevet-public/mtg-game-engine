"""Card class representing a Magic: The Gathering card."""


class Card:
    """Represents a Magic: The Gathering card."""

    def __init__(self, name: str) -> None:
        """
        Initialize a Card.

        Args:
            name: The name of the card.
        """
        self.name = name
