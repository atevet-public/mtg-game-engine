"""Tests for event-derived game logs."""

from mtgengine.card import Card
from mtgengine.event_bus import EventBus
from mtgengine.event_logger import EventLogger
from mtgengine.events import CardDrawnEvent, GameOverEvent
from mtgengine.game_result import GameResult
from mtgengine.player import Player


def test_event_logger_records_shallow_event_fields_in_emission_order() -> None:
    events = EventBus()
    logger = EventLogger(events)
    player = Player("Alice", 20)
    card = Card("Forest", "Land", 0)
    result = GameResult(Player("Bob", 20), player, 4)
    draw = CardDrawnEvent(player, card, 2)
    game_over = GameOverEvent(result)

    events.emit(draw)
    events.emit(game_over)

    assert logger.entries == [
        {"type": "draw", "player": player, "card": card, "cards_remaining": 2},
        {"type": "game_over", "result": result},
    ]


def test_event_logger_subscribes_before_later_handlers() -> None:
    events = EventBus()
    logger = EventLogger(events)
    received: list[bool] = []
    events.subscribe(CardDrawnEvent, lambda _event: received.append(bool(logger.entries)))
    player = Player("Alice", 20)

    events.emit(CardDrawnEvent(player, Card("Island", "Land", 0), 0))

    assert logger.entries[0]["type"] == "draw"
    assert received == [True]
