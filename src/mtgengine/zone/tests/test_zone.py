"""Tests for Zone base class."""

import pytest
from src.mtgengine.zone import Zone
from src.mtgengine.card import Card


class TestZone:
    """Test suite for the base Zone class."""

    def test_zone_initialization(self) -> None:
        """Test Zone initialization."""
        zone = Zone()
        assert zone.cards == []
        assert zone.get_cards() == []

    def test_add_card_to_zone(self) -> None:
        """Test adding a card to a zone."""
        zone = Zone()
        card = Card("Test Card")
        zone.add_card(card)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card

    def test_add_multiple_cards_to_zone(self) -> None:
        """Test adding multiple cards to a zone."""
        zone = Zone()
        card1 = Card("Card 1")
        card2 = Card("Card 2")
        zone.add_card(card1)
        zone.add_card(card2)
        assert len(zone.cards) == 2
        assert zone.cards[0] == card1
        assert zone.cards[1] == card2

    def test_remove_card_from_zone(self) -> None:
        """Test removing a card from a zone."""
        zone = Zone()
        card = Card("Test Card")
        zone.add_card(card)
        zone.remove_card(card)
        assert len(zone.cards) == 0

    def test_remove_card_not_in_zone(self) -> None:
        """Test removing a card that is not in the zone."""
        zone = Zone()
        card1 = Card("Card 1")
        card2 = Card("Card 2")
        zone.add_card(card1)
        zone.remove_card(card2)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card1

    def test_get_cards_returns_copy(self) -> None:
        """Test that get_cards returns a copy of the card list."""
        zone = Zone()
        card = Card("Test Card")
        zone.add_card(card)
        cards = zone.get_cards()
        cards.clear()
        assert len(zone.cards) == 1
