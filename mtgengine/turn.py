from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING
from pyventus.events import EventEmitter, AsyncIOEventEmitter

if TYPE_CHECKING:
    from mtgengine.player import Player


class Phase(Enum):
    """Represents the five phases of a Magic: The Gathering turn."""

    BEGINNING = "beginning"
    PRECOMBAT_MAIN = "precombat main"
    COMBAT = "combat"
    POSTCOMBAT_MAIN = "postcombat main"
    ENDING = "ending"


class Step(Enum):
    """Represents steps within phases."""

    # Beginning phase steps
    UNTAP = "untap"
    UPKEEP = "upkeep"
    DRAW = "draw"

    # Combat phase steps
    BEGIN_COMBAT = "beginning of combat"
    DECLARE_ATTACKERS = "declare attackers"
    DECLARE_BLOCKERS = "declare blockers"
    COMBAT_DAMAGE = "combat damage"
    END_COMBAT = "end of combat"

    # Ending phase steps
    END = "end step"
    CLEANUP = "cleanup"


class Turn:
    def __init__(self, turn_number: int, active_player: Player) -> None:
        """Initialize a Turn with a turn number.

        Args:
            turn_number: The number of the turn in the game.
        """
        self.turn_number = turn_number
        self.active_player = active_player
        self._event_emitter: EventEmitter = AsyncIOEventEmitter()
        self._phase_and_step_events = (
            TurnBeginningPhaseEvent(self),
            TurnUntapStepEvent(self),
            TurnUpkeepStepEvent(self),
            TurnDrawStepEvent(self),
            TurnPrecombatMainPhaseEvent(self),
            TurnCombatPhaseEvent(self),
            TurnBeginningOfCombatStepEvent(self),
            TurnDeclareAttackersStepEvent(self),
            TurnDeclareBlockersStepEvent(self),
            TurnCombatDamageStepEvent(self),
            TurnEndOfCombatStepEvent(self),
            TurnPostcombatMainPhaseEvent(self),
            TurnEndingPhaseEvent(self),
            TurnEndStepEvent(self),
            TurnCleanupStepEvent(self),
        )

    @property
    def phases_and_steps(self):
        """Generator to iterate through the phases and steps of the turn."""
        for event in self._phase_and_step_events:
            self._event_emitter.emit(event)
            yield event


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
