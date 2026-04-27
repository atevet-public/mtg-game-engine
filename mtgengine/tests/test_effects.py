"""Tests for effect classes."""

import pytest

from mtgengine.abilities.effect import (
    DrawCardsEffect,
    GainLifeEffect,
    LoseLifeEffect,
    AddManaEffect,
    PutCounterEffect,
    CreateCreatureTokenEffect,
    DealDamageEffect,
)
from mtgengine.player import Player
from mtgengine.permanent import Permanent
from mtgengine.game import Game
from mtgengine.card import Card
from mtgengine.tests.conftest import make_card_def


class TestDrawCardsEffect:
    """Test suite for the DrawCardsEffect class."""

    def test_draw_cards_effect_description_single(self) -> None:
        """Test description for drawing 1 card."""
        effect = DrawCardsEffect(1)
        assert effect.description() == "Draw 1 card"

    def test_draw_cards_effect_description_multiple(self) -> None:
        """Test description for drawing multiple cards."""
        effect = DrawCardsEffect(3)
        assert effect.description() == "Draw 3 cards"

    def test_draw_cards_effect_resolve(self) -> None:
        """Test resolve() calls controller.draw_from_deck()."""
        player = Player("Test", 20)
        game = Game([player])

        # Add cards to deck
        for _ in range(5):
            player.deck.add_card(Card("Test Card", "Artifact"))

        effect = DrawCardsEffect(2)
        effect.resolve(None, player, [], game)

        # Player should have drawn 2 cards
        assert len(player.hand.get_cards()) == 2

    def test_draw_cards_effect_raises_on_invalid_count(self) -> None:
        """Test DrawCardsEffect raises ValueError for count < 1."""
        with pytest.raises(ValueError, match="count must be at least 1"):
            DrawCardsEffect(0)

        with pytest.raises(ValueError, match="count must be at least 1"):
            DrawCardsEffect(-1)


class TestGainLifeEffect:
    """Test suite for the GainLifeEffect class."""

    def test_gain_life_effect_description(self) -> None:
        """Test description."""
        effect = GainLifeEffect(3)
        assert effect.description() == "Gain 3 life"

    def test_gain_life_effect_resolve(self) -> None:
        """Test resolve() increases controller.life_total."""
        player = Player("Test", 20)
        game = Game([player])

        effect = GainLifeEffect(5)
        effect.resolve(None, player, [], game)

        assert player.life_total == 25


class TestLoseLifeEffect:
    """Test suite for the LoseLifeEffect class."""

    def test_lose_life_effect_description(self) -> None:
        """Test description."""
        effect = LoseLifeEffect(3)
        assert effect.description() == "Lose 3 life"

    def test_lose_life_effect_resolve(self) -> None:
        """Test resolve() decreases controller.life_total."""
        player = Player("Test", 20)
        game = Game([player])

        effect = LoseLifeEffect(5)
        effect.resolve(None, player, [], game)

        assert player.life_total == 15


class TestAddManaEffect:
    """Test suite for the AddManaEffect class."""

    def test_add_mana_effect_description(self) -> None:
        """Test description."""
        effect = AddManaEffect("W", 2)
        assert effect.description() == "Add 2{W}"

    def test_add_mana_effect_resolve(self) -> None:
        """Test resolve() calls controller.mana_pool.add()."""
        player = Player("Test", 20)
        game = Game([player])

        effect = AddManaEffect("R", 3)
        effect.resolve(None, player, [], game)

        assert player.mana_pool.available("R") == 3

    def test_add_mana_effect_raises_on_invalid_color(self) -> None:
        """Test AddManaEffect raises ValueError for invalid color."""
        with pytest.raises(ValueError, match="Invalid mana color"):
            AddManaEffect("X", 1)

    @pytest.mark.parametrize("color", ["W", "U", "B", "R", "G", "C", "generic"])
    def test_add_mana_effect_accepts_valid_colors(self, color: str) -> None:
        """Test AddManaEffect accepts all valid mana colors."""
        effect = AddManaEffect(color, 1)
        assert effect.color == color

    def test_add_mana_effect_raises_on_invalid_amount(self) -> None:
        """Test AddManaEffect raises ValueError for amount < 1."""
        with pytest.raises(ValueError, match="amount must be at least 1"):
            AddManaEffect("W", 0)


class TestPutCounterEffect:
    """Test suite for the PutCounterEffect class."""

    def test_put_counter_effect_description_single(self) -> None:
        """Test description for 1 counter."""
        effect = PutCounterEffect("+1/+1", 1)
        assert effect.description() == "Put 1 +1/+1 counter on target"

    def test_put_counter_effect_description_multiple(self) -> None:
        """Test description for multiple counters."""
        effect = PutCounterEffect("+1/+1", 3)
        assert effect.description() == "Put 3 +1/+1 counters on target"

    def test_put_counter_effect_resolve(self) -> None:
        """Test resolve() calls target.add_counter()."""
        player = Player("Test", 20)
        game = Game([player])
        card_def = make_card_def()
        permanent = Permanent(card_def, player, player)

        effect = PutCounterEffect("+1/+1", 2)
        effect.resolve(None, player, [permanent], game)

        assert permanent.get_counter("+1/+1") == 2

    def test_put_counter_effect_raises_on_invalid_amount(self) -> None:
        """Test PutCounterEffect raises ValueError for amount < 1."""
        with pytest.raises(ValueError, match="amount must be at least 1"):
            PutCounterEffect("+1/+1", 0)


class TestCreateCreatureTokenEffect:
    """Test suite for the CreateCreatureTokenEffect class."""

    def test_create_token_effect_description_single(self) -> None:
        """Test description for 1 token."""
        effect = CreateCreatureTokenEffect(1, 2, 2, "Zombie", ["B"])
        assert effect.description() == "Create 1 2/2 Zombie token"

    def test_create_token_effect_description_multiple(self) -> None:
        """Test description for multiple tokens."""
        effect = CreateCreatureTokenEffect(3, 1, 1, "Goblin", ["R"])
        assert effect.description() == "Create 3 1/1 Goblin tokens"

    def test_create_token_zero_count_raises(self) -> None:
        with pytest.raises(ValueError, match="count must be at least 1"):
            CreateCreatureTokenEffect(0, 1, 1, "Zombie", [])

    def test_create_token_negative_toughness_raises(self) -> None:
        with pytest.raises(ValueError):
            CreateCreatureTokenEffect(1, 1, -1, "Zombie", [])

    def test_create_token_negative_power_allowed(self) -> None:
        # -1/1 tokens are valid in MTG (negative power, positive toughness)
        effect = CreateCreatureTokenEffect(1, -1, 1, "Horror", ["B"])
        assert effect.power == -1


class TestDealDamageEffect:
    """Test suite for the DealDamageEffect class."""

    def test_deal_damage_effect_description(self) -> None:
        """Test description."""
        effect = DealDamageEffect(3)
        assert effect.description() == "Deal 3 damage to target"

    def test_deal_damage_effect_raises_on_invalid_amount(self) -> None:
        """Test DealDamageEffect raises ValueError for amount < 1."""
        with pytest.raises(ValueError, match="amount must be at least 1"):
            DealDamageEffect(0)
