"""Tests for Zone classes."""

import pytest
from src.mtgengine.zone import (
    Zone,
    Battlefield,
    Graveyard,
    Exile,
    Hand,
    Stack,
)
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
        card = Card("Test Card", 2, "Creature")
        zone.add_card(card)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card

    def test_add_multiple_cards_to_zone(self) -> None:
        """Test adding multiple cards to a zone."""
        zone = Zone()
        card1 = Card("Card 1", 1, "Sorcery")
        card2 = Card("Card 2", 2, "Creature")
        zone.add_card(card1)
        zone.add_card(card2)
        assert len(zone.cards) == 2
        assert zone.cards[0] == card1
        assert zone.cards[1] == card2

    def test_remove_card_from_zone(self) -> None:
        """Test removing a card from a zone."""
        zone = Zone()
        card = Card("Test Card", 2, "Creature")
        zone.add_card(card)
        zone.remove_card(card)
        assert len(zone.cards) == 0

    def test_remove_card_not_in_zone(self) -> None:
        """Test removing a card that is not in the zone."""
        zone = Zone()
        card1 = Card("Card 1", 1, "Sorcery")
        card2 = Card("Card 2", 2, "Creature")
        zone.add_card(card1)
        zone.remove_card(card2)
        assert len(zone.cards) == 1
        assert zone.cards[0] == card1

    def test_get_cards_returns_copy(self) -> None:
        """Test that get_cards returns a copy of the card list."""
        zone = Zone()
        card = Card("Test Card", 2, "Creature")
        zone.add_card(card)
        cards = zone.get_cards()
        cards.clear()
        assert len(zone.cards) == 1


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
        card = Card("Creature", 3, "Creature")
        battlefield.add_card(card)
        assert len(battlefield.cards) == 1

    def test_battlefield_is_zone(self) -> None:
        """Test that Battlefield is a Zone."""
        battlefield = Battlefield()
        assert isinstance(battlefield, Zone)


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
        card = Card("Dead Spell", 2, "Sorcery")
        graveyard.add_card(card)
        assert len(graveyard.cards) == 1

    def test_graveyard_is_zone(self) -> None:
        """Test that Graveyard is a Zone."""
        graveyard = Graveyard()
        assert isinstance(graveyard, Zone)


class TestExile:
    """Test suite for the Exile zone."""

    def test_exile_initialization(self) -> None:
        """Test Exile initialization."""
        exile = Exile()
        assert exile.name == "Exile"
        assert exile.cards == []

    def test_exile_add_card(self) -> None:
        """Test adding a card to Exile."""
        exile = Exile()
        card = Card("Exiled Card", 4, "Creature")
        exile.add_card(card)
        assert len(exile.cards) == 1

    def test_exile_is_zone(self) -> None:
        """Test that Exile is a Zone."""
        exile = Exile()
        assert isinstance(exile, Zone)


class TestHand:
    """Test suite for the Hand zone."""

    def test_hand_initialization(self) -> None:
        """Test Hand initialization."""
        hand = Hand()
        assert hand.name == "Hand"
        assert hand.cards == []

    def test_hand_add_card(self) -> None:
        """Test adding a card to Hand."""
        hand = Hand()
        card = Card("Card in Hand", 2, "Instant")
        hand.add_card(card)
        assert len(hand.cards) == 1

    def test_hand_is_zone(self) -> None:
        """Test that Hand is a Zone."""
        hand = Hand()
        assert isinstance(hand, Zone)


class TestStack:
    """Test suite for the Stack zone."""

    def test_stack_initialization(self) -> None:
        """Test Stack initialization."""
        stack = Stack()
        assert stack.name == "Stack"
        assert stack.cards == []

    def test_stack_add_card(self) -> None:
        """Test adding a card to the Stack."""
        stack = Stack()
        card = Card("Stacked Spell", 3, "Sorcery")
        stack.add_card(card)
        assert len(stack.cards) == 1

    def test_stack_is_zone(self) -> None:
        """Test that Stack is a Zone."""
        stack = Stack()
        assert isinstance(stack, Zone)
