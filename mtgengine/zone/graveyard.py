"""Graveyard zone representing the graveyard in Magic: The Gathering."""

from mtgengine.zone import Zone


class Graveyard(Zone):
    """Represents the graveyard zone."""

    def __init__(self) -> None:
        """Initialize the Graveyard zone."""
        super().__init__("Graveyard")
