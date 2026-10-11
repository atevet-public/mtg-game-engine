"""MTG Game Engine package."""

from mtgengine.action_errors import (
    CardNotInHandError,
    DiscardNotRequiredError,
    GameActionError,
    GameNotStartedError,
    GameOverError,
    NoLandDropLeftError,
    NotALandError,
    NotYourTurnError,
    PlayerEliminatedError,
    PlayerNotInGameError,
    WrongPhaseError,
)
from mtgengine.card import Card
from mtgengine.decklist import DecklistEntry, parse_decklist
from mtgengine.game import Game
from mtgengine.game_result import GameResult
from mtgengine.mana_cost import ManaCost
from mtgengine.player import Player
from mtgengine.player_specification import PlayerSpecification
from mtgengine.zone import Zone
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.deck import Deck
from mtgengine.zone.exile import Exile
from mtgengine.zone.graveyard import Graveyard
from mtgengine.zone.hand import Hand
from mtgengine.zone.stack import Stack

__all__ = [
    "Battlefield",
    "Card",
    "CardNotInHandError",
    "Deck",
    "DecklistEntry",
    "DiscardNotRequiredError",
    "Exile",
    "Game",
    "GameActionError",
    "GameNotStartedError",
    "GameOverError",
    "GameResult",
    "Graveyard",
    "Hand",
    "ManaCost",
    "NoLandDropLeftError",
    "NotALandError",
    "NotYourTurnError",
    "Player",
    "PlayerEliminatedError",
    "PlayerNotInGameError",
    "PlayerSpecification",
    "Stack",
    "WrongPhaseError",
    "Zone",
    "parse_decklist",
]
