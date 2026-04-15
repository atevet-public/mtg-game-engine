"""Cost class hierarchy for Magic: The Gathering ability costs."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mtgengine.permanent import Permanent
    from mtgengine.player import Player

from mtgengine.mana_cost import ManaCost as MtgManaCost


class Cost(ABC):
    """Abstract base for all ability costs."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable cost description."""

    @abstractmethod
    def can_pay(self, source: Permanent, controller: Player) -> bool:
        """Return True if the cost can currently be paid."""

    @abstractmethod
    def pay(self, source: Permanent, controller: Player) -> None:
        """Pay the cost. Raises ValueError if cost cannot be paid."""


class ManaCost(Cost):
    """A mana payment cost. Uses the ManaPool on the controller."""

    def __init__(self, mana_cost: MtgManaCost) -> None:
        # MtgManaCost = mtgengine.mana_cost.ManaCost (renamed to avoid collision)
        self._mana_cost = mana_cost

    def description(self) -> str:
        return str(self._mana_cost)

    def can_pay(self, source: Permanent, controller: Player) -> bool:
        # Simplified: check generic + colored. Full spending logic in Phase 5.
        return controller.mana_pool.total() >= self._mana_cost.mana_value()

    def pay(self, source: Permanent, controller: Player) -> None:
        if not self.can_pay(source, controller):
            raise ValueError("Insufficient mana to pay cost")
        # Full mana payment logic deferred to Phase 5.


class TapCost(Cost):
    """{T}: tap the source permanent."""

    def description(self) -> str:
        return "{T}"

    def can_pay(self, source: Permanent, controller: Player) -> bool:
        return not source.tapped and not source.summoning_sick

    def pay(self, source: Permanent, controller: Player) -> None:
        if not self.can_pay(source, controller):
            raise ValueError(
                "Cannot tap: permanent is already tapped or has summoning sickness"
            )
        source.tap()


class SacrificeCost(Cost):
    """Sacrifice the source permanent (or a permanent matching a filter)."""

    def __init__(self, description_text: str = "this permanent") -> None:
        self._description_text = description_text

    def description(self) -> str:
        return f"Sacrifice {self._description_text}"

    def can_pay(self, source: Permanent, controller: Player) -> bool:
        # Source is always sacrificeable as long as it's on the battlefield under your control
        return source.controller is controller

    def pay(self, source: Permanent, controller: Player) -> None:
        if not self.can_pay(source, controller):
            raise ValueError("Cannot sacrifice: you don't control this permanent")
        # Actual zone transition (battlefield → graveyard) implemented in Phase 4/5.


class DiscardCost(Cost):
    """Discard a card from hand."""

    def __init__(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError("count must be at least 1")
        self.count = count

    def description(self) -> str:
        return f"Discard {self.count} card{'s' if self.count > 1 else ''}"

    def can_pay(self, source: Permanent, controller: Player) -> bool:
        return len(controller.hand.get_cards()) >= self.count

    def pay(self, source: Permanent, controller: Player) -> None:
        if not self.can_pay(source, controller):
            raise ValueError("Not enough cards in hand to discard")
        # Actual discard (hand → graveyard) implemented in Phase 4/5.


class CompoundCost(Cost):
    """A combination of multiple costs that must all be paid together."""

    def __init__(self, *costs: Cost) -> None:
        if len(costs) < 2:
            raise ValueError("CompoundCost requires at least 2 costs")
        self.costs = list(costs)

    def description(self) -> str:
        return ", ".join(c.description() for c in self.costs)

    def can_pay(self, source: Permanent, controller: Player) -> bool:
        return all(c.can_pay(source, controller) for c in self.costs)

    def pay(self, source: Permanent, controller: Player) -> None:
        if not self.can_pay(source, controller):
            raise ValueError(
                "Cannot pay compound cost: one or more costs cannot be paid"
            )
        # NOTE(Phase 4): This pay() loop is not transactional. If a sub-cost's
        # pay() raises after earlier costs have already mutated state, those
        # mutations are not rolled back. Before Phase 5 (casting/cost payment),
        # this must be made atomic (e.g., snapshot/restore or two-phase commit).
        for cost in self.costs:
            cost.pay(source, controller)
