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

    def __init__(self, name: str, life_total: int) -> None:
        """Initialize a Player with name, life total, and game zones.

        Args:
            name: The player's name.
            life_total: The player's starting life total.

        Notes:
            ``events`` is assigned by ``Game`` so player-driven actions can publish
            events to that game's subscribers.
        """
        self.name = name
        self.life_total = life_total
        self.deck = Deck()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.exile = Exile()
        self.events = EventBus()

    def draw_from_deck(self, n: int) -> list[Card]:
        """Draw up to n cards individually and add each to the player's hand.

        Args:
            n: Number of cards to draw.
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
