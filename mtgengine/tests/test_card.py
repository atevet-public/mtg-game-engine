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
        assert card.owner_index is None

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

    def test_card_tap_sets_tapped_flag(self) -> None:
        """Calling tap should mark the card as tapped."""
        card = Card("Grizzly Bears", card_type="Creature")
        assert card.tapped is False

        card.tap()
        assert card.tapped is True

    def test_card_untap_clears_tapped_flag(self) -> None:
        """Calling untap should clear the tapped state."""
        card = Card("Llanowar Elves", card_type="Creature")
        card.tap()
        assert card.tapped is True

        card.untap()
        assert card.tapped is False

    @pytest.mark.parametrize("owner_index", [0, 1])
    def test_card_sets_owner_index(self, owner_index: int) -> None:
        """Card should store explicit owner index for shared zones."""
        card = Card("Owning Player Permanent", card_type="Creature", owner_index=owner_index)
        assert card.owner_index == owner_index

    @pytest.mark.parametrize(
        ("owner_index", "expected_exception"),
        [
            (True, TypeError),
            ("0", TypeError),
            (-1, ValueError),
        ],
    )
    def test_card_rejects_invalid_owner_index(
        self, owner_index: object, expected_exception: type[Exception]
    ) -> None:
        """Card should reject bool/non-int/negative owner indexes."""
        with pytest.raises(expected_exception):
            Card("Invalid Owner", card_type="Creature", owner_index=owner_index)  # type: ignore[arg-type]
