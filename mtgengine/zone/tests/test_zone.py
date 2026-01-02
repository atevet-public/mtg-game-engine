"""Tests for Zone base class."""

from mtgengine.card import Card
from mtgengine.zone import Zone


class TestZone:
    """Test suite for the base Zone class."""

    def test_zone_initialization(self) -> None:
        """Test Zone initialization."""
        zone = Zone("Test Zone")
        assert zone.name == "Test Zone"
        assert zone.cards == []
        assert zone.get_cards() == []

    def test_add_card_to_zone(self) -> None:
        """Test adding a card to a zone."""
        zone = Zone("Test Zone")
        card = Card("Test Card", card_type="Creature")
        zone.add_card(card)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card

    def test_add_multiple_cards_to_zone(self) -> None:
        """Test adding multiple cards to a zone."""
        zone = Zone("Test Zone")
        card1 = Card("Card 1", card_type="Creature")
        card2 = Card("Card 2", card_type="Creature")
        zone.add_card(card1)
        zone.add_card(card2)
        assert len(zone.cards) == 2
        assert zone.cards[0] == card1
        assert zone.cards[1] == card2

    def test_remove_card_from_zone(self) -> None:
        """Test removing a card from a zone."""
        zone = Zone("Test Zone")
        card = Card("Test Card", card_type="Creature")
        zone.add_card(card)
        zone.remove_card(card)
        assert len(zone.cards) == 0

    def test_remove_card_not_in_zone(self) -> None:
        """Test removing a card that is not in the zone."""
        zone = Zone("Test Zone")
        card1 = Card("Card 1", card_type="Creature")
        card2 = Card("Card 2", card_type="Creature")
        zone.add_card(card1)
        zone.remove_card(card2)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card1

    def test_get_cards_returns_copy(self) -> None:
        """Test that get_cards returns a copy of the card list."""
        zone = Zone("Test Zone")
        card = Card("Test Card", card_type="Creature")
        zone.add_card(card)
        cards = zone.get_cards()
        cards.clear()
        assert len(zone.cards) == 1
