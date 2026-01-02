"""Tests for Card class."""

import pytest
from src.mtgengine.card import Card


class TestCard:
    """Test suite for the Card class."""

    def test_card_initialization(self) -> None:
        """Test Card initialization with all parameters."""
        card = Card("Lightning Bolt", 1, "Sorcery")
        assert card.name == "Lightning Bolt"
        assert card.mana_cost == 1
        assert card.card_type == "Sorcery"

    def test_card_with_different_values(self) -> None:
        """Test Card with various property values."""
        card = Card("Black Lotus", 0, "Artifact")
        assert card.name == "Black Lotus"
        assert card.mana_cost == 0
        assert card.card_type == "Artifact"

    def test_card_with_high_mana_cost(self) -> None:
        """Test Card with high mana cost."""
        card = Card("Emrakul", 15, "Creature")
        assert card.name == "Emrakul"
        assert card.mana_cost == 15
        assert card.card_type == "Creature"
