"""Player class representing a Magic: The Gathering player."""

from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand


class Player:
    """Represents a Magic: The Gathering player."""

    def __init__(self, name: str, life_total: int) -> None:
        """Initialize a Player with name, life total, and game zones.

        Args:
            name: The player's name.
            life_total: The player's starting life total.
        """
        self.name = name
        self.life_total = life_total
        self.deck = Deck()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.exile = Exile()
        self.battlefield = Battlefield()
