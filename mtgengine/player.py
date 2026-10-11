"""Player class representing a Magic: The Gathering player."""

from __future__ import annotations

from mtgengine.card import Card
from mtgengine.event_bus import EventBus
from mtgengine.events import CardDrawnEvent, EmptyDeckDrawAttemptedEvent
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand


class Player:
    """Represents a Magic: The Gathering player."""

    def __init__(
        self,
        name: str,
        life_total: int,
        *,
        maximum_hand_size: int = 7,
    ) -> None:
        """Initialize a Player with name, life total, and game zones.

        Args:
            name: The player's name.
            life_total: The player's starting life total.
            maximum_hand_size: The number of cards allowed at cleanup; defaults to seven.

        Notes:
            ``events`` is assigned by ``Game`` so player-driven actions can publish
            events to that game's subscribers.
        """
        self.name = name
        self.life_total = life_total
        self.maximum_hand_size = maximum_hand_size
        self.deck = Deck()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.exile = Exile()
        self.events = EventBus()

    @property
    def maximum_hand_size(self) -> int:
        """The number of cards this player may hold at cleanup."""
        return self._maximum_hand_size

    @maximum_hand_size.setter
    def maximum_hand_size(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Maximum Hand Size must be an integer")
        if value < 0:
            raise ValueError("Maximum Hand Size must not be negative")
        self._maximum_hand_size = value

    @property
    def exceeds_maximum_hand_size(self) -> bool:
        """Whether the current hand requires a discard at cleanup."""
        return len(self.hand.get_cards()) > self.maximum_hand_size

    def draw_from_deck(self, n: int) -> list[Card]:
        """Draw up to n cards individually and add each to the player's hand.

        Args:
            n: Number of cards to draw.

        Returns:
            The cards successfully drawn before the deck became empty.
        """
        cards: list[Card] = []
        for _ in range(n):
            if not self.deck.get_cards():
                self.events.emit(EmptyDeckDrawAttemptedEvent(self))
                break
            card = self.deck.draw(1)[0]
            self.hand.add_card(card)
            cards.append(card)
            self.events.emit(CardDrawnEvent(self, card, len(self.deck.get_cards())))
        return cards
