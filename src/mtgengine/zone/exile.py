"""Exile zone representing exile in Magic: The Gathering."""

from src.mtgengine.zone import Zone


class Exile(Zone):
    """Represents the exile zone."""

    def __init__(self) -> None:
        """Initialize the Exile zone."""
        super().__init__()
        self.name = "Exile"
