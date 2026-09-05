"""Player class representing a Magic: The Gathering player."""

from pyventus.events import EventLinker

from mtgengine.turn import TurnUntapStepEvent
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand


@EventLinker.on(TurnUntapStepEvent)
def handle_untap_step(event: TurnUntapStepEvent) -> None:
    """Handle the untap step event by untapping permanents of the active player.

    Args:
        event: The turn untap step event containing the turn and active player.
    """
    active_player = event.turn.active_player
    for permanent in active_player.battlefield.get_cards():
        permanent.untap()


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

    def draw_from_deck(self, n: int) -> None:
        """Draw n cards from the deck and add them to the player's hand.

        Args:
            n: Number of cards to draw.
        """
        cards = self.deck.draw(n)
        for card in cards:
            self.hand.add_card(card)
