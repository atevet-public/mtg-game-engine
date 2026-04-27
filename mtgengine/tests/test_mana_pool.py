"""Tests for ManaPool class."""

import pytest

from mtgengine.mana_pool import ManaPool


class TestManaPool:
    """Test suite for the ManaPool class."""

    def test_mana_pool_initialization(self) -> None:
        """Test ManaPool initializes empty."""
        pool = ManaPool()
        assert pool.total() == 0
        assert pool.available("W") == 0
        assert pool.available("U") == 0
        assert pool.available("B") == 0
        assert pool.available("R") == 0
        assert pool.available("G") == 0
        assert pool.available("C") == 0

    def test_add_mana(self) -> None:
        """Test adding mana to the pool."""
        pool = ManaPool()
        pool.add("W", 2)
        assert pool.available("W") == 2
        assert pool.total() == 2

        pool.add("U", 3)
        assert pool.available("U") == 3
        assert pool.total() == 5

    def test_add_mana_default_amount(self) -> None:
        """Test adding mana defaults to 1."""
        pool = ManaPool()
        pool.add("R")
        assert pool.available("R") == 1

    def test_add_mana_accumulates(self) -> None:
        """Test adding mana to existing color accumulates."""
        pool = ManaPool()
        pool.add("G", 2)
        pool.add("G", 3)
        assert pool.available("G") == 5

    def test_add_invalid_color_raises(self) -> None:
        """Test adding invalid color raises ValueError."""
        pool = ManaPool()
        with pytest.raises(ValueError, match="Invalid mana color"):
            pool.add("X", 1)

    def test_add_zero_amount_raises(self) -> None:
        """Test adding zero or negative amount raises ValueError."""
        pool = ManaPool()
        with pytest.raises(ValueError, match="Amount must be at least 1"):
            pool.add("W", 0)
        with pytest.raises(ValueError, match="Amount must be at least 1"):
            pool.add("W", -1)

    def test_spend_mana_success(self) -> None:
        """Test spending available mana succeeds."""
        pool = ManaPool()
        pool.add("B", 5)
        assert pool.spend("B", 2) is True
        assert pool.available("B") == 3

    def test_spend_mana_all(self) -> None:
        """Test spending all mana of a color."""
        pool = ManaPool()
        pool.add("R", 3)
        assert pool.spend("R", 3) is True
        assert pool.available("R") == 0
        assert pool.total() == 0

    def test_spend_mana_insufficient(self) -> None:
        """Test spending more mana than available fails."""
        pool = ManaPool()
        pool.add("W", 2)
        assert pool.spend("W", 3) is False
        assert pool.available("W") == 2  # unchanged

    def test_spend_mana_none_available(self) -> None:
        """Test spending when none available fails."""
        pool = ManaPool()
        assert pool.spend("U", 1) is False

    def test_spend_mana_default_amount(self) -> None:
        """Test spend defaults to 1."""
        pool = ManaPool()
        pool.add("G", 2)
        assert pool.spend("G") is True
        assert pool.available("G") == 1

    def test_empty_pool(self) -> None:
        """Test emptying the mana pool."""
        pool = ManaPool()
        pool.add("W", 2)
        pool.add("U", 3)
        pool.add("R", 1)
        assert pool.total() == 6

        pool.empty()
        assert pool.total() == 0
        assert pool.available("W") == 0
        assert pool.available("U") == 0
        assert pool.available("R") == 0

    def test_total_mana(self) -> None:
        """Test total returns sum of all mana."""
        pool = ManaPool()
        pool.add("W", 1)
        pool.add("U", 2)
        pool.add("B", 3)
        pool.add("R", 4)
        pool.add("G", 5)
        pool.add("C", 6)
        assert pool.total() == 21

    def test_repr(self) -> None:
        """Test string representation."""
        pool = ManaPool()
        pool.add("W", 2)
        pool.add("U", 1)
        repr_str = repr(pool)
        assert "ManaPool" in repr_str
        assert "W" in repr_str
        assert "U" in repr_str

    def test_spend_zero_amount_raises(self) -> None:
        """Test spending zero amount raises ValueError."""
        pool = ManaPool()
        pool.add("W", 3)
        with pytest.raises(ValueError, match="Amount must be at least 1"):
            pool.spend("W", 0)

    def test_spend_negative_amount_raises(self) -> None:
        """Test spending negative amount raises ValueError."""
        pool = ManaPool()
        pool.add("W", 3)
        with pytest.raises(ValueError, match="Amount must be at least 1"):
            pool.spend("W", -1)

    def test_available_invalid_color_raises(self) -> None:
        """Test available with invalid color raises ValueError."""
        pool = ManaPool()
        with pytest.raises(ValueError, match="Invalid mana color"):
            pool.available("X")

    def test_spend_invalid_color_raises(self) -> None:
        """Test spend with invalid color raises ValueError."""
        pool = ManaPool()
        with pytest.raises(ValueError, match="Invalid mana color"):
            pool.spend("X", 1)
