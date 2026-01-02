"""Tests for Card class."""

import pytest

from src.mtgengine.card import Card


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
