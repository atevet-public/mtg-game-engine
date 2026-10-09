"""Result of a finished game."""

from dataclasses import dataclass

from mtgengine.player import Player


@dataclass(frozen=True)
class GameResult:
    """The winner, loser, ending Turn Number, and reason for a finished game."""

    winner: Player
    loser: Player
    turn_number: int
    reason: str = "empty_library"
