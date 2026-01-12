"""Card class representing a Magic: The Gathering card."""

from __future__ import annotations

from typing import Iterable

from mtgengine.mana_cost import ManaCost


VALID_CARD_TYPES = frozenset(
    {
        "Creature",
        "Instant",
        "Sorcery",
        "Enchantment",
        "Artifact",
        "Planeswalker",
        "Land",
        "Battle",
    }
)


class Card:
    """Represents a Magic: The Gathering card with validated characteristics."""

    def __init__(
        self,
        name: str,
        card_type: str,
        mana_cost: ManaCost | None = None,
        color_indicator: Iterable[str] | None = None,
        supertypes: Iterable[str] | None = None,
        subtypes: Iterable[str] | None = None,
        rules_text: str = "",
        power: int | None = None,
        toughness: int | None = None,
        loyalty: int | None = None,
        defense: int | None = None,
    ) -> None:
        """Initialize a Card.

        Args:
            name: The name of the card.
            card_type: The primary card type (validated).
            mana_cost: The mana cost of the card. Defaults to zero cost.
            color_indicator: Optional iterable of color symbols (e.g. {'W', 'U'}).
            supertypes: Optional iterable of supertypes.
            subtypes: Optional iterable of subtypes.
            rules_text: Oracle/rules text of the card.
            power: Power (int) or None. Must be non-negative if int.
            toughness: Toughness (int) or None. Must be non-negative if int.
            loyalty: Loyalty (int) or None. Must be non-negative if int.
            defense: Defense (int) or None. Must be non-negative if int.
        """
        self.name = name
        # card_type is required and must be one of the valid types
        if card_type not in VALID_CARD_TYPES:
            raise ValueError(f"Invalid card type: {card_type}")
        self.card_type = card_type

        # mana_cost defaults to zero cost
        self.mana_cost = mana_cost or ManaCost()

        # Normalise iterables to concrete container types
        self.color_indicator = set(color_indicator or ())
        self.supertypes = list(supertypes or ())
        self.subtypes = list(subtypes or ())

        self.rules_text = rules_text

        # Simple tapped state for turn-based actions (e.g., untap step)
        self.tapped = False

        # Numeric characteristics: must be int or None and non-negative
        for field_name, value in (
            ("power", power),
            ("toughness", toughness),
            ("loyalty", loyalty),
            ("defense", defense),
        ):
            if value is not None and not isinstance(value, int):
                raise TypeError(f"{field_name} must be int or None")
            if isinstance(value, int) and value < 0:
                raise ValueError(f"{field_name} must be non-negative")
            setattr(self, field_name, value)

    def tap(self) -> None:
        """Mark the card as tapped."""
        self.tapped = True

    def untap(self) -> None:
        """Mark the card as untapped."""
        self.tapped = False

