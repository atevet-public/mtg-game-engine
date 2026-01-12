from dataclasses import dataclass
from mtgengine.player import Player
from pyventus.events import EventEmitter, AsyncIOEventEmitter


class Turn:
    def __init__(self, turn_number: int, active_player: Player) -> None:
        """Initialize a Turn with a turn number.

        Args:
            turn_number: The number of the turn in the game.
        """
        self.turn_number = turn_number
        self.active_player = active_player
        self._event_emitter: EventEmitter = AsyncIOEventEmitter()
        self._steps = [TurnUntapStepEvent(self)]

    @property
    def steps(self):
        """Generator to iterate through the phases of the turn."""
        for event in self._steps:
            self._event_emitter.emit(event)
            yield event


@dataclass
class TurnUntapStepEvent:
    turn: Turn
