"""MTG Game Engine package."""

from mtgengine.card import Card
from mtgengine.decklist import DecklistEntry, parse_decklist
from mtgengine.game import Game, GameResult, PlayerSpecification
from mtgengine.mana_cost import ManaCost
from mtgengine.player import Player
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
    "Deck",
    "DecklistEntry",
    "Exile",
    "Game",
    "GameResult",
    "Graveyard",
    "Hand",
    "ManaCost",
    "Player",
    "PlayerSpecification",
    "Stack",
    "Zone",
    "parse_decklist",
]
