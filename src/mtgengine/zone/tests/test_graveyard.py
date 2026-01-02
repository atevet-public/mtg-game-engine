"""Tests for Graveyard zone."""

from src.mtgengine.card import Card
from src.mtgengine.zone import Zone
from src.mtgengine.zone.graveyard import Graveyard


class TestGraveyard:
    """Test suite for the Graveyard zone."""

    def test_graveyard_initialization(self) -> None:
        """Test Graveyard initialization."""
        graveyard = Graveyard()
        assert graveyard.name == "Graveyard"
        assert graveyard.cards == []

    def test_graveyard_add_card(self) -> None:
        """Test adding a card to the Graveyard."""
        graveyard = Graveyard()
        card = Card("Dead Spell")
        graveyard.add_card(card)
        assert len(graveyard.cards) == 1

    def test_graveyard_is_zone(self) -> None:
        """Test that Graveyard is a Zone."""
        graveyard = Graveyard()
        assert isinstance(graveyard, Zone)
