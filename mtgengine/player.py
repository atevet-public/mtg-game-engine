"""Player class representing a Magic: The Gathering player."""


class Player:
    """Represents a Magic: The Gathering player."""

    def __init__(self, name: str, life_total: int) -> None:
        """
        Initialize a Player.

        Args:
            name: The name of the player.
            life_total: The player's starting life total.
        """
        self.name = name
        self.life_total = life_total
