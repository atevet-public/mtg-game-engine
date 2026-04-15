"""Ability class hierarchy for Magic: The Gathering card abilities."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Any

from mtgengine.abilities.cost import Cost
from mtgengine.abilities.effect import Effect, ContinuousEffect


class Ability(ABC):
    """Abstract base for all Magic: The Gathering card abilities."""

    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this ability."""


class ActivatedAbility(Ability):
    """
    An ability with a cost that a player may activate at any time they have priority
    (subject to timing restrictions). Format: '{cost}: {effect}'.
    Goes on the stack when activated.
    """

    def __init__(
        self,
        cost: Cost,  # from mtgengine.abilities.cost
        effect: Effect,  # from mtgengine.abilities.effect
        sorcery_speed: bool = False,  # True = can only activate at sorcery speed (main phase, empty stack)
    ) -> None:
        self.cost = cost
        self.effect = effect
        self.sorcery_speed = sorcery_speed

    def description(self) -> str:
        return f"{self.cost.description()}: {self.effect.description()}"


class TriggeredAbility(Ability):
    """
    An ability that triggers automatically when a specific game event occurs.
    Format: 'When/Whenever/At {trigger_condition}, {effect}'.
    Goes on the stack when triggered.
    """

    def __init__(
        self,
        trigger_event_type: type,  # the pyventus event class that triggers this ability
        condition: Callable[[Any], bool] | None,  # optional extra filter on the event
        effect: Effect,
    ) -> None:
        self.trigger_event_type = trigger_event_type
        self.condition = condition
        self.effect = effect

    def matches(self, event: Any) -> bool:
        """Return True if this ability triggers on the given event."""
        if not isinstance(event, self.trigger_event_type):
            return False
        if self.condition is not None:
            return self.condition(event)
        return True

    def description(self) -> str:
        cond = f" (if {self.condition.__name__})" if self.condition else ""
        return f"Triggered by {self.trigger_event_type.__name__}{cond}: {self.effect.description()}"


class StaticAbility(Ability):
    """
    A continuous ability that is always 'on' while the source is in the appropriate zone.
    Never uses the stack. Examples: flying (evasion), +1/+1 to creatures you control.
    """

    def __init__(self, effect: ContinuousEffect) -> None:  # ContinuousEffect from effect.py
        self.effect = effect

    def description(self) -> str:
        return self.effect.description()
