"""Turn structure, phases, steps, and events for MTG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from pyventus.events import EventEmitter, AsyncIOEventEmitter

if TYPE_CHECKING:
    from mtgengine.player import Player


class Turn:
    def __init__(self, turn_number: int, active_player: Player) -> None:
        """Initialize a Turn with a turn number.

        Args:
            turn_number: The number of the turn in the game.
            active_player: The player whose turn it is.
        """
        self.turn_number = turn_number
        self.active_player = active_player
        self._event_emitter: EventEmitter = AsyncIOEventEmitter()
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
            self._event_emitter.emit(event_instance)
            yield event_instance


@dataclass
class TurnBeginningPhaseEvent:
    turn: Turn


@dataclass
class TurnUntapStepEvent:
    turn: Turn


@dataclass
class TurnUpkeepStepEvent:
    turn: Turn


@dataclass
class TurnDrawStepEvent:
    turn: Turn


@dataclass
class TurnPrecombatMainPhaseEvent:
    turn: Turn


@dataclass
class TurnCombatPhaseEvent:
    turn: Turn


@dataclass
class TurnBeginningOfCombatStepEvent:
    turn: Turn


@dataclass
class TurnDeclareAttackersStepEvent:
    turn: Turn


@dataclass
class TurnDeclareBlockersStepEvent:
    turn: Turn


@dataclass
class TurnCombatDamageStepEvent:
    turn: Turn


@dataclass
class TurnEndOfCombatStepEvent:
    turn: Turn


@dataclass
class TurnPostcombatMainPhaseEvent:
    turn: Turn


@dataclass
class TurnEndingPhaseEvent:
    turn: Turn


@dataclass
class TurnEndStepEvent:
    turn: Turn


@dataclass
class TurnCleanupStepEvent:
    turn: Turn
