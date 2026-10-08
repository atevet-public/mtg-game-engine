"""Validation of parsed decklists for the MVP game."""

from mtgengine.decklist import DecklistEntry

BASIC_LANDS = frozenset({"Plains", "Island", "Swamp", "Mountain", "Forest"})
MINIMUM_DECK_SIZE = 60


def validate(entries: list[DecklistEntry], name: str) -> None:
    """Validate that a deck is at least 60 cards and contains only basic lands.

    Args:
        entries: Parsed decklist entries.
        name: Player name used in error messages.

    Raises:
        ValueError: If the deck is too small or contains a non-basic-land card.
    """
    if sum(entry.quantity for entry in entries) < MINIMUM_DECK_SIZE:
        raise ValueError(f"Player {name!r} deck must contain at least 60 cards")
    if any(entry.name not in BASIC_LANDS for entry in entries):
        raise ValueError(f"Player {name!r} deck may contain only basic lands")
