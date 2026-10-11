"""Result of a finished game."""

from dataclasses import dataclass, field

from mtgengine.player import Player


@dataclass(frozen=True, init=False)
class GameResult:
    """The winner, players who lost, ending Turn Number, and ending reason.

    During a multiplayer game, ``winner`` is ``None`` while more than one player
    remains; ``losers`` accumulates losses until the game has a winner.
    """

    winner: Player | None
    _losers: tuple[Player, ...] = field(repr=False)
    turn_number: int
    reason: str = "empty_library"

    def __init__(
        self,
        winner: Player | None,
        losers: list[Player],
        turn_number: int,
        reason: str = "empty_library",
    ) -> None:
        """Create a game-loss record.

        Args:
            winner: The winning player, or ``None`` while multiplayer play continues.
            losers: Players who have lost so far.
            turn_number: Turn Number when this result was recorded.
            reason: Why a player lost; defaults to ``empty_library``.
        """
        object.__setattr__(self, "winner", winner)
        object.__setattr__(self, "_losers", tuple(losers))
        object.__setattr__(self, "turn_number", turn_number)
        object.__setattr__(self, "reason", reason)

    @property
    def losers(self) -> list[Player]:
        """Return a copy of the Players who have lost so callers cannot alter game state."""
        return list(self._losers)
