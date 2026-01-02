"""Tests for Stack zone."""

import pytest
from src.mtgengine.stack import Stack
from src.mtgengine.zone import Zone
from src.mtgengine.card import Card


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
        card = Card("Stacked Spell")
        stack.add_card(card)
        assert len(stack.cards) == 1

    def test_stack_is_zone(self) -> None:
        """Test that Stack is a Zone."""
        stack = Stack()
        assert isinstance(stack, Zone)
