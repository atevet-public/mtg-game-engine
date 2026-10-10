"""Domain events emitted by game actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from mtgengine.card import Card

if TYPE_CHECKING:
    from mtgengine.game_result import GameResult
    from mtgengine.player import Player


@dataclass(frozen=True)
class CardDrawnEvent:
    player: Player
    card: Card
    cards_remaining: int
    log_name: ClassVar[str] = "draw"


@dataclass(frozen=True)
class EmptyDeckDrawAttemptedEvent:
    player: Player
    log_name: ClassVar[str] = "empty_deck_draw_attempted"


@dataclass(frozen=True)
class GameOverEvent:
    result: GameResult
    log_name: ClassVar[str] = "game_over"


@dataclass(frozen=True)
class StartingPlayerSelectedEvent:
    player: Player
    log_name: ClassVar[str] = "starting_player"


@dataclass(frozen=True)
class LandPlayedEvent:
    player: Player
    card: Card
    log_name: ClassVar[str] = "land_drop"


@dataclass(frozen=True)
class CardDiscardedEvent:
    player: Player
    card: Card
    log_name: ClassVar[str] = "discard"
