"""Stack zone representing the stack in Magic: The Gathering."""

from src.mtgengine.zone import Zone


class Stack(Zone):
    """Represents the stack zone."""

    def __init__(self) -> None:
        """Initialize the Stack zone."""
        super().__init__()
        self.name = "Stack"
