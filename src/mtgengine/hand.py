"""Hand zone representing a player's hand in Magic: The Gathering."""

from src.mtgengine.zone import Zone


class Hand(Zone):
    """Represents a player's hand zone."""

    def __init__(self) -> None:
        """Initialize the Hand zone."""
        super().__init__()
        self.name = "Hand"
