"""Tests for Battlefield zone."""

import pytest

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
        card = Card("Creature", card_type="Creature", owner_index=0)
        battlefield.add_card(card)
        assert len(battlefield.cards) == 1

    def test_battlefield_add_card_requires_owner_index(self) -> None:
        """Test that cards must have owner_index to enter battlefield."""
        battlefield = Battlefield()
        card = Card("Creature", card_type="Creature")

        with pytest.raises(ValueError, match="owner_index"):
            battlefield.add_card(card)

    def test_battlefield_add_card_rejects_invalid_owner_index(self) -> None:
        """Test that invalid owner_index values are rejected at add time."""
        battlefield = Battlefield()
        card = Card("Creature", card_type="Creature", owner_index=0)
        card.owner_index = -1

        with pytest.raises(ValueError, match="owner_index"):
            battlefield.add_card(card)

    def test_battlefield_is_zone(self) -> None:
        """Test that Battlefield is a Zone."""
        battlefield = Battlefield()
        assert isinstance(battlefield, Zone)
