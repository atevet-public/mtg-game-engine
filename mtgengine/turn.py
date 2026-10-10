"""Turn structure, phases, steps, and events for MTG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from mtgengine.event_bus import EventBus
    from mtgengine.player import Player


class Turn:
    def __init__(self, turn_number: int, active_player: Player, events: EventBus) -> None:
        """Initialize a Turn with a turn number.

        Args:
            turn_number: The number of the turn in the game.
            active_player: The player whose turn it is.
            events: The event bus shared by the game and its turns.
        """
        self.turn_number = turn_number
        self.active_player = active_player
        self._events = events
        self._phase_and_step_events = (
            TurnBeginningPhaseEvent,
            TurnUntapStepEvent,
            TurnUpkeepStepEvent,
            TurnDrawStepEvent,
            TurnPrecombatMainPhaseEvent,
            TurnCombatPhaseEvent,
            TurnBeginningOfCombatStepEvent,
            TurnDeclareAttackersStepEvent,
            TurnDeclareBlockersStepEvent,
            TurnCombatDamageStepEvent,
            TurnEndOfCombatStepEvent,
            TurnPostcombatMainPhaseEvent,
            TurnEndingPhaseEvent,
            TurnEndStepEvent,
            TurnCleanupStepEvent,
        )

    @property
    def phases_and_steps(self):
        """Generator to iterate through the phases and steps of the turn."""
        for event in self._phase_and_step_events:
            event_instance = event(self)
            self._events.emit(event_instance)
            yield event_instance


@dataclass
class TurnBeginningPhaseEvent:
    turn: Turn
    log_name: ClassVar[str] = "beginning_phase"


@dataclass
class TurnUntapStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "untap_step"


@dataclass
class TurnUpkeepStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "upkeep_step"


@dataclass
class TurnDrawStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "draw_step"


@dataclass
class TurnPrecombatMainPhaseEvent:
    turn: Turn
    log_name: ClassVar[str] = "first_main_phase"


@dataclass
class TurnCombatPhaseEvent:
    turn: Turn
    log_name: ClassVar[str] = "combat_phase"


@dataclass
class TurnBeginningOfCombatStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "beginning_of_combat_step"


@dataclass
class TurnDeclareAttackersStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "declare_attackers_step"


@dataclass
class TurnDeclareBlockersStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "declare_blockers_step"


@dataclass
class TurnCombatDamageStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "combat_damage_step"


@dataclass
class TurnEndOfCombatStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "end_of_combat_step"


@dataclass
class TurnPostcombatMainPhaseEvent:
    turn: Turn
    log_name: ClassVar[str] = "second_main_phase"


@dataclass
class TurnEndingPhaseEvent:
    turn: Turn
    log_name: ClassVar[str] = "ending_phase"


@dataclass
class TurnEndStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "end_step"


@dataclass
class TurnCleanupStepEvent:
    turn: Turn
    log_name: ClassVar[str] = "cleanup_step"
