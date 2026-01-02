"""Tests for Stack zone."""

from mtgengine.card import Card
from mtgengine.zone import Zone
from mtgengine.zone.stack import Stack


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
        card = Card("Stacked Spell", card_type="Instant")
        stack.add_card(card)
        assert len(stack.cards) == 1

    def test_stack_is_zone(self) -> None:
        """Test that Stack is a Zone."""
        stack = Stack()
        assert isinstance(stack, Zone)
