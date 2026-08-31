"""Tests for Player class."""

import pytest
from pyventus.events import AsyncIOEventEmitter

from mtgengine.card import Card
from mtgengine.game import Game
from mtgengine.player import Player, handle_untap_step
from mtgengine.turn import TurnUntapStepEvent
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

    def test_player_untap_step_untaps_only_active_player_permanents(self) -> None:
        """Test that untap step only untaps active player's permanents."""
        active_player = Player("Active", 20)
        non_active_player = Player("Non Active", 20)
        game = Game([active_player, non_active_player])
        turn = type("TurnStub", (), {"active_player": active_player, "turn_number": 1})()

        active_permanent = Card("Active Permanent", card_type="Creature", owner_index=0)
        active_permanent.tap()

        non_active_permanent = Card("Non Active Permanent", card_type="Creature", owner_index=1)
        non_active_permanent.tap()

        game.battlefield.add_card(active_permanent)
        game.battlefield.add_card(non_active_permanent)

        event_emitter = AsyncIOEventEmitter()
        event_emitter.emit(TurnUntapStepEvent(turn))

        assert active_permanent.tapped is False
        assert non_active_permanent.tapped is True

    def test_player_untap_step_noops_when_active_player_has_no_game(self) -> None:
        """Test that untap handling is a safe no-op with no attached game."""
        active_player = Player("Active", 20)
        turn = type("TurnStub", (), {"active_player": active_player, "turn_number": 1})()
        event = TurnUntapStepEvent(turn)

        handle_untap_step(event)

        assert active_player.game is None

    def test_player_untap_step_noops_when_active_player_not_in_game_players(self) -> None:
        """Test untap handling safely no-ops if active player is not indexed in game."""
        active_player = Player("Active", 20)
        game_player = Player("In Game", 20)
        game = Game([game_player])
        active_player.game = game
        turn = type("TurnStub", (), {"active_player": active_player, "turn_number": 1})()
        event = TurnUntapStepEvent(turn)

        handle_untap_step(event)


def test_player_does_not_own_battlefield_zone() -> None:
    player = Player("Alice", 20)
    assert not hasattr(player, "battlefield")
