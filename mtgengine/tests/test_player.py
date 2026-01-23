"""Tests for Player class."""

from unittest.mock import Mock
import pytest

from mtgengine.player import Player
from mtgengine.turn import TurnUntapStepEvent
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand

from pyventus.events import AsyncIOEventEmitter


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
        assert isinstance(player.battlefield, Battlefield)

    def test_player_zones_are_empty(self) -> None:
        """Test that a player's zones start empty."""
        player = Player("Test", 20)
        assert len(player.deck.get_cards()) == 0
        assert len(player.hand.get_cards()) == 0
        assert len(player.graveyard.get_cards()) == 0
        assert len(player.exile.get_cards()) == 0
        assert len(player.battlefield.get_cards()) == 0

    def test_player_untap_step(self) -> None:
        """Test that the player's untap step untaps all permanents they control."""
        active_player = Player("Active", 20)
        turn = Mock(active_player=active_player, turn_number=1)

        # Add a tapped permanent to the active player's battlefield
        card = Mock()
        active_player.battlefield.add_card(card)

        # Emit the untap step event
        event_emitter = AsyncIOEventEmitter()
        event_emitter.emit(TurnUntapStepEvent(turn))

        # Verify that the card was untapped
        card.untap.assert_called_once()
