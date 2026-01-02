"""Tests for Exile zone."""

import pytest
from src.mtgengine.exile import Exile
from src.mtgengine.zone import Zone
from src.mtgengine.card import Card


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
        card = Card("Exiled Card")
        exile.add_card(card)
        assert len(exile.cards) == 1

    def test_exile_is_zone(self) -> None:
        """Test that Exile is a Zone."""
        exile = Exile()
        assert isinstance(exile, Zone)
