"""Effect class hierarchy for Magic: The Gathering ability effects."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mtgengine.player import Player
    from mtgengine.game import Game


class Effect(ABC):
    """Abstract base for one-shot effects that resolve from the stack."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @abstractmethod
    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        """Execute the effect. Called when the stack object resolves."""


class ContinuousEffect(ABC):
    """Abstract base for continuous effects that are always active (from StaticAbility)."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @abstractmethod
    def apply(self, game: Game) -> None:
        """Apply this effect to the game state. Called every time game state is evaluated."""


class DrawCardsEffect(Effect):
    """Draw N cards."""

    def __init__(self, count: int) -> None:
        if count < 1:
            raise ValueError("count must be at least 1")
        self.count = count

    def description(self) -> str:
        return f"Draw {self.count} card{'s' if self.count > 1 else ''}"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        controller.draw_from_deck(self.count)


class DealDamageEffect(Effect):
    """Deal N damage to a target (player or permanent)."""

    def __init__(self, amount: int) -> None:
        if amount < 1:
            raise ValueError("amount must be at least 1")
        self.amount = amount

    def description(self) -> str:
        return f"Deal {self.amount} damage to target"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        # Full damage application logic implemented in Phase 4/5.
        pass  # TODO(Phase 4): apply damage to targets


class GainLifeEffect(Effect):
    """Gain N life."""

    def __init__(self, amount: int) -> None:
        if amount < 1:
            raise ValueError("amount must be at least 1")
        self.amount = amount

    def description(self) -> str:
        return f"Gain {self.amount} life"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        controller.life_total += self.amount


class LoseLifeEffect(Effect):
    """Lose N life."""

    def __init__(self, amount: int) -> None:
        if amount < 1:
            raise ValueError("amount must be at least 1")
        self.amount = amount

    def description(self) -> str:
        return f"Lose {self.amount} life"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        controller.life_total -= self.amount


class AddManaEffect(Effect):
    """Add mana to the controller's mana pool."""

    def __init__(self, color: str, amount: int = 1) -> None:
        from mtgengine.mana_pool import MANA_COLORS

        if color not in MANA_COLORS and color != "generic":
            raise ValueError(f"Invalid mana color: {color}")
        if amount < 1:
            raise ValueError("amount must be at least 1")
        self.color = color
        self.amount = amount

    def description(self) -> str:
        return f"Add {self.amount}{{{self.color}}}"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        controller.mana_pool.add(self.color, self.amount)


class DestroyEffect(Effect):
    """Destroy target permanent."""

    def description(self) -> str:
        return "Destroy target permanent"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        pass  # TODO(Phase 4): move target to graveyard (respecting indestructible)


class ExileEffect(Effect):
    """Exile target card."""

    def description(self) -> str:
        return "Exile target"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        pass  # TODO(Phase 4): move target to exile zone


class CounterSpellEffect(Effect):
    """Counter target spell."""

    def description(self) -> str:
        return "Counter target spell"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        pass  # TODO(Phase 4): remove target from stack


class CreateTokenEffect(Effect):
    """Create one or more creature tokens."""

    def __init__(
        self, count: int, power: int, toughness: int, name: str, colors: list[str]
    ) -> None:
        if count < 1:
            raise ValueError("count must be at least 1")
        if toughness < 0:
            raise ValueError("toughness cannot be negative")
        # Note: power CAN be negative (e.g., -1/-1 tokens exist in MTG)
        self.count = count
        self.power = power
        self.toughness = toughness
        self.name = name
        self.colors = colors

    def description(self) -> str:
        return f"Create {self.count} {self.power}/{self.toughness} {self.name} token{'s' if self.count > 1 else ''}"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        pass  # TODO(Phase 4): create token permanents on battlefield


class PutCounterEffect(Effect):
    """Put N counters of a given type on a target permanent."""

    def __init__(self, counter_type: str, amount: int = 1) -> None:
        if amount < 1:
            raise ValueError("amount must be at least 1")
        self.counter_type = counter_type
        self.amount = amount

    def description(self) -> str:
        return f"Put {self.amount} {self.counter_type} counter{'s' if self.amount > 1 else ''} on target"

    def resolve(
        self, source: Any, controller: Player, targets: list[Any], game: Game
    ) -> None:
        for target in targets:
            if hasattr(target, "add_counter"):
                target.add_counter(self.counter_type, self.amount)
