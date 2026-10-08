"""Result of a finished game."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GameResult:
    """The winner, loser, ending Turn Number, and reason for a finished game."""

    winner_name: str
    loser_name: str
    turn_number: int
    reason: str = "empty_library"
