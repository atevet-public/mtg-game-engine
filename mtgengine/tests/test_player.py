"""Tests for Player class."""

import pytest

from mtgengine.card import Card
from mtgengine.events import CardDrawnEvent, EmptyDeckDrawAttemptedEvent
from mtgengine.game import Game
from mtgengine.player import Player
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand


class TestPlayer:
    """Test suite for the Player class."""

    @pytest.mark.parametrize(
        "name,life_total",
        [
            ("Alice", 20),
            ("Bob", 40),
            ("Charlie", 0),
        ],
    )
    def test_player_initialization(
        self,
        name: str,
        life_total: int,
    ) -> None:
        """Test Player initialization with various parameters."""
        player = Player(name, life_total)
        assert player.name == name
        assert player.life_total == life_total

    def test_player_has_zones(self) -> None:
        """Test that a player has all required zones."""
        player = Player("Test", 20)
        assert isinstance(player.deck, Deck)
        assert isinstance(player.hand, Hand)
        assert isinstance(player.graveyard, Graveyard)
        assert isinstance(player.exile, Exile)

    def test_player_zones_are_empty(self) -> None:
        """Test that a player's zones start empty."""
        player = Player("Test", 20)
        assert len(player.deck.get_cards()) == 0
        assert len(player.hand.get_cards()) == 0
        assert len(player.graveyard.get_cards()) == 0
        assert len(player.exile.get_cards()) == 0

    def test_draw_from_deck_emits_one_event_per_card_with_remaining_count(self) -> None:
        player = Player("Alice", 20)
        game = Game([player, Player("Bob", 20)])
        bottom_card = Card("Bottom", "Land", 0)
        top_card = Card("Top", "Land", 0)
        player.deck.add_card(bottom_card)
        player.deck.add_card(top_card)
        received: list[CardDrawnEvent] = []
        game.events.subscribe(CardDrawnEvent, received.append)

        drawn = player.draw_from_deck(2)

        assert drawn == [top_card, bottom_card]
        assert player.hand.get_cards() == [top_card, bottom_card]
        assert received == [
            CardDrawnEvent(player, top_card, 1),
            CardDrawnEvent(player, bottom_card, 0),
        ]

    def test_draw_from_deck_keeps_partial_draw_and_emits_one_empty_deck_attempt(self) -> None:
        player = Player("Alice", 20)
        game = Game([player, Player("Bob", 20)])
        card = Card("Only card", "Land", 0)
        player.deck.add_card(card)
        draws: list[CardDrawnEvent] = []
        failures: list[EmptyDeckDrawAttemptedEvent] = []
        game.events.subscribe(CardDrawnEvent, draws.append)
        game.events.subscribe(EmptyDeckDrawAttemptedEvent, failures.append)

        drawn = player.draw_from_deck(3)

        assert drawn == [card]
        assert player.hand.get_cards() == [card]
        assert draws == [CardDrawnEvent(player, card, 0)]
        assert failures == [EmptyDeckDrawAttemptedEvent(player)]

    def test_player_untap_step_untaps_only_active_player_permanents(self) -> None:
        """Test that untap step only untaps active player's permanents."""
        active_player = Player("Active", 20)
        non_active_player = Player("Non Active", 20)
        game = Game([active_player, non_active_player])
        active_permanent = Card("Active Permanent", card_type="Creature", owner_index=0)
        active_permanent.tap()

        non_active_permanent = Card("Non Active Permanent", card_type="Creature", owner_index=1)
        non_active_permanent.tap()

        game.battlefield.add_card(active_permanent)
        game.battlefield.add_card(non_active_permanent)

        game.perform_untap_step()

        assert active_permanent.tapped is False
        assert non_active_permanent.tapped is True


def test_player_does_not_own_battlefield_zone() -> None:
    player = Player("Alice", 20)
    assert not hasattr(player, "battlefield")
