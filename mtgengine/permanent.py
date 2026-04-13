"""Permanent class representing a card on the battlefield."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mtgengine.card_definition import CardDefinition
    from mtgengine.player import Player


class Permanent:
    """Represents a card that has resolved onto the battlefield."""

    def __init__(
        self,
        definition: CardDefinition,
        owner: Player,
        controller: Player,
    ) -> None:
        """Initialize a Permanent with definition, owner, and controller.

        Args:
            definition: The card definition this permanent is based on.
            owner: The player who owns this permanent.
            controller: The player who currently controls this permanent.
        """
        self.definition = definition
        self.owner = owner
        self.controller = controller
        self.tapped: bool = False
        self.summoning_sick: bool = True
        self.counters: dict[str, int] = {}
        self.attached_to: Permanent | None = None
        self.attachments: list[Permanent] = []

    def tap(self) -> None:
        """Tap this permanent.

        Raises:
            ValueError: If permanent is already tapped.
        """
        if self.tapped:
            raise ValueError(f"{self.definition.name} is already tapped")
        self.tapped = True

    def untap(self) -> None:
        """Untap this permanent."""
        self.tapped = False

    def add_counter(self, counter_type: str, amount: int = 1) -> None:
        """Add counters of the given type.

        Args:
            counter_type: Type of counter (e.g., "+1/+1", "loyalty").
            amount: Number of counters to add (default: 1).
        """
        self.counters[counter_type] = self.counters.get(counter_type, 0) + amount

    def remove_counter(self, counter_type: str, amount: int = 1) -> None:
        """Remove counters of the given type. Counter count cannot go below 0.

        Args:
            counter_type: Type of counter to remove.
            amount: Number of counters to remove (default: 1).
        """
        current = self.counters.get(counter_type, 0)
        new_value = max(0, current - amount)
        if new_value == 0:
            self.counters.pop(counter_type, None)
        else:
            self.counters[counter_type] = new_value

    def get_counter(self, counter_type: str) -> int:
        """Get count of counters of the given type.

        Args:
            counter_type: Type of counter to query.

        Returns:
            Number of counters of that type.
        """
        return self.counters.get(counter_type, 0)
