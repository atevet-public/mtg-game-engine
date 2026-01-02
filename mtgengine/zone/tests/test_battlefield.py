"""Tests for Battlefield zone."""

from mtgengine.card import Card
from mtgengine.zone import Zone
from mtgengine.zone.battlefield import Battlefield


class TestBattlefield:
    """Test suite for the Battlefield zone."""

    def test_battlefield_initialization(self) -> None:
        """Test Battlefield initialization."""
        battlefield = Battlefield()
        assert battlefield.name == "Battlefield"
        assert battlefield.cards == []

    def test_battlefield_add_card(self) -> None:
        """Test adding a card to the Battlefield."""
        battlefield = Battlefield()
        card = Card("Creature")
        battlefield.add_card(card)
        assert len(battlefield.cards) == 1

    def test_battlefield_is_zone(self) -> None:
        """Test that Battlefield is a Zone."""
        battlefield = Battlefield()
        assert isinstance(battlefield, Zone)
