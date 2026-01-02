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
        card = Card(name, card_type="Instant")
        assert card.name == name
        assert isinstance(card.mana_cost, ManaCost)
        assert card.mana_cost.mana_value() == 0

    def test_card_with_mana_cost(self) -> None:
        """Test Card initialization with explicit mana cost."""
        cost = ManaCost(red=1)
        card = Card("Lightning Bolt", card_type="Instant", mana_cost=cost)
        assert card.name == "Lightning Bolt"
        assert card.mana_cost is cost

    def test_invalid_card_type_raises(self) -> None:
        """Invalid card type should raise ValueError."""
        with pytest.raises(ValueError):
            Card("Foo", card_type="InvalidType")

    def test_numeric_fields_type_and_non_negative(self) -> None:
        """Numeric fields must be int or None and non-negative."""
        # Wrong type
        with pytest.raises(TypeError):
            Card("BadPower", card_type="Creature", power="five")  # type: ignore[arg-type]

        # Negative value
        with pytest.raises(ValueError):
            Card("NegTough", card_type="Creature", toughness=-1)

