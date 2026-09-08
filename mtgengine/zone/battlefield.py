"""Battlefield zone representing the battlefield in Magic: The Gathering."""

from mtgengine.zone import Zone


class Battlefield(Zone):
    """Represents the battlefield zone."""

    def __init__(self) -> None:
        """Initialize the Battlefield zone."""
        super().__init__("Battlefield")
