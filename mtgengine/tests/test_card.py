"""Tests for Card class."""

import pytest

from mtgengine.card import Card
from mtgengine.mana_cost import ManaCost


class TestCard:
    """Test suite for the Card class."""

    @pytest.mark.parametrize(
        "name",
        [
            "Lightning Bolt",
        ],
    )
    def test_card_initialization(self, name: str) -> None:
        """Test Card initialization with name."""
        card = Card(name)
        assert card.name == name
        assert isinstance(card.mana_cost, ManaCost)
        assert card.mana_cost.mana_value() == 0

    def test_card_with_mana_cost(self) -> None:
        """Test Card initialization with explicit mana cost."""
        cost = ManaCost(red=1)
        card = Card("Lightning Bolt", mana_cost=cost)
        assert card.name == "Lightning Bolt"
        assert card.mana_cost is cost
