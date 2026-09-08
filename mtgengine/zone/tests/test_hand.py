"""Tests for Hand zone."""

from mtgengine.card import Card
from mtgengine.zone import Zone
from mtgengine.zone.hand import Hand


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
        card = Card("Card in Hand", card_type="Creature", owner_index=1)
        hand.add_card(card)
        assert len(hand.cards) == 1

    def test_hand_is_zone(self) -> None:
        """Test that Hand is a Zone."""
        hand = Hand()
        assert isinstance(hand, Zone)
