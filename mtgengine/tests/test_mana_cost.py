"""Tests for ManaCost class."""

import pytest

from mtgengine.mana_cost import ManaCost


class TestManaCost:
    """Test suite for the ManaCost class."""

    def test_manacost_initialization_default(self) -> None:
        """Test ManaCost initialization with default values."""
        cost = ManaCost()
        assert cost.white == 0
        assert cost.blue == 0
        assert cost.black == 0
        assert cost.red == 0
        assert cost.green == 0
        assert cost.colorless == 0
        assert cost.generic == 0

    def test_manacost_initialization_with_values(self) -> None:
        """Test ManaCost initialization with explicit values."""
        cost = ManaCost(white=2, blue=1, generic=3)
        assert cost.white == 2
        assert cost.blue == 1
        assert cost.black == 0
        assert cost.red == 0
        assert cost.green == 0
        assert cost.colorless == 0
        assert cost.generic == 3

    def test_manacost_total_cost(self) -> None:
        """Test ManaCost mana_value() method."""
        cost = ManaCost(white=2, blue=1, generic=3)
        assert cost.mana_value() == 6

    def test_manacost_total_cost_includes_all_types(self) -> None:
        """Test that mana_value includes all color and generic types."""
        cost = ManaCost(white=1, blue=1, black=1, red=1, green=1, colorless=1, generic=2)
        assert cost.mana_value() == 8

    def test_manacost_from_notation_generic_only(self) -> None:
        """Test parsing generic mana only."""
        cost = ManaCost.from_notation("5")
        assert cost.generic == 5
        assert cost.mana_value() == 5

    def test_manacost_from_notation_color_only(self) -> None:
        """Test parsing color mana only."""
        cost = ManaCost.from_notation("WUB")
        assert cost.white == 1
        assert cost.blue == 1
        assert cost.black == 1
        assert cost.mana_value() == 3

    def test_manacost_from_notation_mixed(self) -> None:
        """Test parsing mixed generic and color mana."""
        cost = ManaCost.from_notation("2WUB")
        assert cost.generic == 2
        assert cost.white == 1
        assert cost.blue == 1
        assert cost.black == 1
        assert cost.mana_value() == 5

    def test_manacost_from_notation_repeated_colors(self) -> None:
        """Test parsing repeated color mana."""
        cost = ManaCost.from_notation("2RRG")
        assert cost.generic == 2
        assert cost.red == 2
        assert cost.green == 1
        assert cost.mana_value() == 5

    def test_manacost_from_notation_empty(self) -> None:
        """Test parsing empty notation (zero cost)."""
        cost = ManaCost.from_notation("")
        assert cost.mana_value() == 0

    def test_manacost_from_notation_colorless(self) -> None:
        """Test parsing colorless mana."""
        cost = ManaCost.from_notation("CC")
        assert cost.colorless == 2
        assert cost.mana_value() == 2

    def test_manacost_from_notation_mixed_with_colorless(self) -> None:
        """Test parsing mixed costs including colorless."""
        cost = ManaCost.from_notation("1WCC")
        assert cost.generic == 1
        assert cost.white == 1
        assert cost.colorless == 2
        assert cost.mana_value() == 4

    def test_manacost_from_notation_invalid_character(self) -> None:
        """Test that invalid characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid mana notation character"):
            ManaCost.from_notation("2X")

    def test_manacost_negative_values_raise_error(self) -> None:
        """Test that negative mana costs raise ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            ManaCost(white=-1)

    def test_manacost_is_immutable(self) -> None:
        """Test that ManaCost is frozen (immutable)."""
        cost = ManaCost(white=1)
        with pytest.raises(AttributeError):
            cost.white = 2  # type: ignore
