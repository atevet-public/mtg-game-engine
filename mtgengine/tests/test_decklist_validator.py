"""Tests for decklist validation."""

import pytest

from mtgengine.decklist import DecklistEntry
from mtgengine.decklist_validator import validate


def entry(name: str, quantity: int) -> DecklistEntry:
    return DecklistEntry(quantity, name, None, None)


def test_validate_accepts_sixty_basic_lands() -> None:
    validate([entry("Forest", 30), entry("Island", 30)], "Alice")


def test_validate_rejects_fewer_than_sixty_cards() -> None:
    with pytest.raises(ValueError, match="at least 60 cards"):
        validate([entry("Forest", 59)], "Alice")


def test_validate_rejects_non_basic_lands() -> None:
    with pytest.raises(ValueError, match="only basic lands"):
        validate([entry("Forest", 60), entry("Sol Ring", 1)], "Alice")


def test_validate_error_includes_player_name() -> None:
    with pytest.raises(ValueError, match="'Alice'"):
        validate([entry("Forest", 1)], "Alice")
