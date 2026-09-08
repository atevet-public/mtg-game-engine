"""Player class representing a Magic: The Gathering player."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyventus.events import EventLinker

from mtgengine.turn import TurnUntapStepEvent
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand

if TYPE_CHECKING:
    from mtgengine.game import Game


@EventLinker.on(TurnUntapStepEvent)
def handle_untap_step(event: TurnUntapStepEvent) -> None:
    """Handle untap by untapping only active player's shared-battlefield permanents.

    Args:
        event: The turn untap step event containing the turn and active player.
    """
    active_player = event.turn.active_player
    assert active_player is not None

    if active_player.game is None:
        raise AttributeError("Active player has no game attached.")
    try:
        active_player_index = active_player.game.players.index(active_player)
    except ValueError:
        return
    for permanent in active_player.game.battlefield.get_cards():
        if permanent.owner_index == active_player_index:
            permanent.untap()


class Player:
    """Represents a Magic: The Gathering player."""

    def __init__(self, name: str, life_total: int) -> None:
        """Initialize a Player with name, life total, and game zones.

        Args:
            name: The player's name.
            life_total: The player's starting life total.

        Notes:
            ``game`` is intentionally a back-reference set by ``Game`` so player-driven
            events (like untap handling) can resolve shared zones and turn context.
        """
        self.name = name
        self.life_total = life_total
        self.deck = Deck()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.exile = Exile()
        # Intentional back-reference for turn/event handlers that need game state.
        self.game: Game | None = None

    def draw_from_deck(self, n: int) -> None:
        """Draw n cards from the deck and add them to the player's hand.

        Args:
            n: Number of cards to draw.
        """
        cards = self.deck.draw(n)
        for card in cards:
            self.hand.add_card(card)
