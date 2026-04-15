"""Tests for cost classes."""

import pytest

from mtgengine.abilities.cost import (
    TapCost,
    SacrificeCost,
    DiscardCost,
    CompoundCost,
    ManaCost,
)
from mtgengine.mana_cost import ManaCost as MtgManaCost
from mtgengine.permanent import Permanent
from mtgengine.player import Player
from mtgengine.card_definition import CardDefinition
from mtgengine.card import Card


def make_card_def(name: str = "Test") -> CardDefinition:
    """Helper to create a simple CardDefinition for testing."""
    return CardDefinition(
        oracle_id="test-id",
        name=name,
        mana_cost="{0}",
        type_line="Artifact",
        oracle_text=None,
        colors=[],
        color_identity=[],
        keywords=[],
        power=None,
        toughness=None,
        loyalty=None,
        layout="normal",
    )


class TestTapCost:
    """Test suite for the TapCost class."""

    def test_tap_cost_description(self) -> None:
        """Test TapCost description is {T}."""
        cost = TapCost()
        assert cost.description() == "{T}"

    def test_tap_cost_can_pay_when_ready(self) -> None:
        """Test can_pay returns True when permanent is untapped and not summoning sick."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = False
        permanent.summoning_sick = False

        cost = TapCost()
        assert cost.can_pay(permanent, player) is True

    def test_tap_cost_can_pay_false_when_tapped(self) -> None:
        """Test can_pay returns False when permanent is tapped."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = True
        permanent.summoning_sick = False

        cost = TapCost()
        assert cost.can_pay(permanent, player) is False

    def test_tap_cost_can_pay_false_when_summoning_sick(self) -> None:
        """Test can_pay returns False when permanent has summoning sickness."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = False
        permanent.summoning_sick = True

        cost = TapCost()
        assert cost.can_pay(permanent, player) is False

    def test_tap_cost_pay_taps_permanent(self) -> None:
        """Test pay() taps the permanent."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = False
        permanent.summoning_sick = False

        cost = TapCost()
        cost.pay(permanent, player)

        assert permanent.tapped is True

    def test_tap_cost_pay_raises_when_cannot_pay(self) -> None:
        """Test pay() raises ValueError when cost cannot be paid."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = True
        permanent.summoning_sick = False

        cost = TapCost()
        with pytest.raises(ValueError, match="Cannot tap"):
            cost.pay(permanent, player)


class TestSacrificeCost:
    """Test suite for the SacrificeCost class."""

    def test_sacrifice_cost_description_default(self) -> None:
        """Test SacrificeCost description with default text."""
        cost = SacrificeCost()
        assert cost.description() == "Sacrifice sacrifice this permanent"

    def test_sacrifice_cost_description_custom(self) -> None:
        """Test SacrificeCost description with custom text."""
        cost = SacrificeCost("a creature")
        assert cost.description() == "Sacrifice a creature"

    def test_sacrifice_cost_can_pay_when_controller_matches(self) -> None:
        """Test can_pay returns True when controller matches."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        cost = SacrificeCost()
        assert cost.can_pay(permanent, player) is True

    def test_sacrifice_cost_can_pay_false_when_controller_different(self) -> None:
        """Test can_pay returns False when controller doesn't match."""
        owner = Player("Owner", 20)
        controller = Player("Controller", 20)
        other_player = Player("Other", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, owner, controller)

        cost = SacrificeCost()
        assert cost.can_pay(permanent, other_player) is False


class TestDiscardCost:
    """Test suite for the DiscardCost class."""

    def test_discard_cost_description_single_card(self) -> None:
        """Test DiscardCost description for 1 card."""
        cost = DiscardCost(1)
        assert cost.description() == "Discard 1 card"

    def test_discard_cost_description_multiple_cards(self) -> None:
        """Test DiscardCost description for multiple cards."""
        cost = DiscardCost(3)
        assert cost.description() == "Discard 3 cards"

    def test_discard_cost_can_pay_when_enough_cards(self) -> None:
        """Test can_pay returns True when hand has enough cards."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        # Add cards to hand
        for _ in range(3):
            player.hand.add_card(Card("Test Card", "Artifact"))

        cost = DiscardCost(2)
        assert cost.can_pay(permanent, player) is True

    def test_discard_cost_can_pay_false_when_not_enough_cards(self) -> None:
        """Test can_pay returns False when hand doesn't have enough cards."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        # Add only 1 card to hand
        player.hand.add_card(Card("Test Card", "Artifact"))

        cost = DiscardCost(2)
        assert cost.can_pay(permanent, player) is False

    def test_discard_cost_raises_on_invalid_count(self) -> None:
        """Test DiscardCost raises ValueError for count < 1."""
        with pytest.raises(ValueError, match="count must be at least 1"):
            DiscardCost(0)

        with pytest.raises(ValueError, match="count must be at least 1"):
            DiscardCost(-1)


class TestCompoundCost:
    """Test suite for the CompoundCost class."""

    def test_compound_cost_description(self) -> None:
        """Test CompoundCost description joins costs with commas."""
        cost1 = TapCost()
        cost2 = DiscardCost(1)
        compound = CompoundCost(cost1, cost2)

        assert compound.description() == "{T}, Discard 1 card"

    def test_compound_cost_can_pay_all_true(self) -> None:
        """Test can_pay returns True when all costs can be paid."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = False
        permanent.summoning_sick = False

        # Add card to hand for discard
        player.hand.add_card(Card("Test Card", "Artifact"))

        cost1 = TapCost()
        cost2 = DiscardCost(1)
        compound = CompoundCost(cost1, cost2)

        assert compound.can_pay(permanent, player) is True

    def test_compound_cost_can_pay_one_false(self) -> None:
        """Test can_pay returns False when one cost cannot be paid."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = True  # Can't pay tap cost
        permanent.summoning_sick = False

        # Add card to hand for discard
        player.hand.add_card(Card("Test Card", "Artifact"))

        cost1 = TapCost()
        cost2 = DiscardCost(1)
        compound = CompoundCost(cost1, cost2)

        assert compound.can_pay(permanent, player) is False

    def test_compound_cost_pay_calls_all_costs(self) -> None:
        """Test pay() calls pay on all costs."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)
        permanent.tapped = False
        permanent.summoning_sick = False

        # Add card to hand for discard
        player.hand.add_card(Card("Test Card", "Artifact"))

        cost1 = TapCost()
        cost2 = SacrificeCost()
        compound = CompoundCost(cost1, cost2)

        # Should tap the permanent
        compound.pay(permanent, player)
        assert permanent.tapped is True

    def test_compound_cost_raises_on_less_than_two_costs(self) -> None:
        """Test CompoundCost raises ValueError for less than 2 costs."""
        with pytest.raises(ValueError, match="CompoundCost requires at least 2 costs"):
            CompoundCost(TapCost())

        with pytest.raises(ValueError, match="CompoundCost requires at least 2 costs"):
            CompoundCost()


class TestManaCost:
    """Test suite for the ManaCost class."""

    def test_mana_cost_description(self) -> None:
        """Test ManaCost description uses str(mana_cost)."""
        mana_cost = MtgManaCost.from_notation("2W")
        cost = ManaCost(mana_cost)

        assert cost.description() == "2W"

    def test_mana_cost_can_pay_sufficient_mana(self) -> None:
        """Test can_pay returns True when controller has enough mana."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        # Add mana to pool
        player.mana_pool.add("W", 1)
        player.mana_pool.add("generic", 2)

        mana_cost = MtgManaCost.from_notation("2W")
        cost = ManaCost(mana_cost)

        assert cost.can_pay(permanent, player) is True

    def test_mana_cost_can_pay_insufficient_mana(self) -> None:
        """Test can_pay returns False when controller doesn't have enough mana."""
        player = Player("Test", 20)
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        # Only add 1 mana (need 3)
        player.mana_pool.add("W", 1)

        mana_cost = MtgManaCost.from_notation("2W")
        cost = ManaCost(mana_cost)

        assert cost.can_pay(permanent, player) is False
