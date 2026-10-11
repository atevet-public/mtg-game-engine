"""Typed errors raised when a player action is not legal in the current game state."""

from typing import ClassVar


class GameActionError(Exception):
    """Base class for rejected player actions, with a stable machine-readable code."""

    code: ClassVar[str] = "game_action_error"


class GameNotStartedError(GameActionError):
    """Raised when a player action is attempted before the game starts."""

    code: ClassVar[str] = "game_not_started"


class GameOverError(GameActionError):
    """Raised when a player action is attempted after the game ends."""

    code: ClassVar[str] = "game_over"


class NotYourTurnError(GameActionError):
    """Raised when a player other than the Active Player attempts an action."""

    code: ClassVar[str] = "not_your_turn"


class WrongPhaseError(GameActionError):
    """Raised when an action is attempted outside its legal phase or step."""

    code: ClassVar[str] = "wrong_phase"


class CardNotInHandError(GameActionError):
    """Raised when the named card is not in the player's hand."""

    code: ClassVar[str] = "card_not_in_hand"


class NotALandError(GameActionError):
    """Raised when the named card is in hand but is not a land."""

    code: ClassVar[str] = "not_a_land"


class NoLandDropLeftError(GameActionError):
    """Raised when the player has already used their Land Drop this turn."""

    code: ClassVar[str] = "no_land_drop_left"


class DiscardNotRequiredError(GameActionError):
    """Raised when the hand does not exceed its Maximum Hand Size."""

    code: ClassVar[str] = "discard_not_required"


class PlayerNotInGameError(GameActionError):
    """Raised when a command references a player outside this game."""

    code: ClassVar[str] = "player_not_in_game"


class PlayerEliminatedError(GameActionError):
    """Raised when a command is attempted by a player who has lost the game."""

    code: ClassVar[str] = "player_eliminated"
