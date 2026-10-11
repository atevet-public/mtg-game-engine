"""Tests for player-driven game actions."""

import pytest

from mtgengine.action_errors import (
    CardNotInHandError,
    DiscardNotRequiredError,
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
from mtgengine.game import Game
from mtgengine.game_result import GameResult
from mtgengine.player import Player
from mtgengine.turn import (
    TurnBeginningPhaseEvent,
    TurnCleanupStepEvent,
    TurnPrecombatMainPhaseEvent,
    TurnUntapStepEvent,
)


def game_with_opening_decks(maximum_hand_size: int = 7) -> Game:
    game = Game(
        [Player("Alice", 20), Player("Bob", 20)],
        maximum_hand_size=maximum_hand_size,
        auto_play_land=False,
        auto_discard=False,
    )
    for player_index, player in enumerate(game.players):
        for card_number in range(10):
            player.deck.add_card(Card(f"Forest {card_number}", "Land", player_index))
    game.start_game()
    return game


def test_move_advances_exactly_one_phase_or_step() -> None:
    game = game_with_opening_decks()

    first_event = game.move()
    second_event = game.move()

    assert isinstance(first_event, TurnBeginningPhaseEvent)
    assert isinstance(second_event, TurnUntapStepEvent)
    assert [entry["type"] for entry in game.event_log[-2:]] == ["beginning_phase", "untap_step"]


def test_pass_turn_fast_forwards_to_the_first_available_land_action() -> None:
    game = game_with_opening_decks()
    active_player = game.turn.active_player
    land = Card("Chosen Forest", "Land", game.players.index(active_player))
    active_player.hand.add_card(land)

    event = game.pass_turn()

    assert isinstance(event, TurnPrecombatMainPhaseEvent)
    assert game.turn.active_player is active_player
    assert [entry["type"] for entry in game.event_log[-5:]] == [
        "beginning_phase",
        "untap_step",
        "upkeep_step",
        "draw_step",
        "first_main_phase",
    ]


def test_play_land_matches_case_insensitively_and_moves_only_the_named_card() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    land = Card("Chosen Forest", "Land", game.players.index(player))
    other_land = Card("Other Forest", "Land", game.players.index(player))
    player.hand.add_card(land)
    player.hand.add_card(other_land)
    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)

    game.play_land(player, "cHoSeN fOrEsT")

    assert game.battlefield.get_cards() == [land]
    assert player.hand.get_cards()[-1] is other_land


def test_play_land_rejects_wrong_player_wrong_phase_and_a_second_land_drop() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    other_player = next(candidate for candidate in game.players if candidate is not player)
    land = Card("Chosen Forest", "Land", game.players.index(player))
    player.hand.add_card(land)
    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)

    with pytest.raises(NotYourTurnError) as wrong_player:
        game.play_land(other_player, "Chosen Forest")
    assert wrong_player.value.code == "not_your_turn"

    game.play_land(player, "Chosen Forest")
    with pytest.raises(NoLandDropLeftError) as second_drop:
        game.play_land(player, "Chosen Forest")
    assert second_drop.value.code == "no_land_drop_left"


def test_play_land_rejects_calls_outside_a_main_phase_and_missing_cards() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    with pytest.raises(WrongPhaseError) as wrong_phase:
        game.play_land(player, "Missing Forest")
    assert wrong_phase.value.code == "wrong_phase"

    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)
    with pytest.raises(CardNotInHandError) as missing_card:
        game.play_land(player, "Missing Forest")
    assert missing_card.value.code == "card_not_in_hand"


def test_play_land_rejects_nonlands_in_hand() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    spell = Card("Lightning Bolt", "Instant", game.players.index(player))
    player.hand.add_card(spell)
    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)

    with pytest.raises(NotALandError) as not_a_land:
        game.play_land(player, spell.name)
    assert not_a_land.value.code == "not_a_land"


def test_pass_turn_stops_for_required_cleanup_discard() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    land = Card("Chosen Forest", "Land", game.players.index(player))
    player.hand.add_card(land)
    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)
    game.play_land(player, land.name)
    discarded = Card("Discard me", "Creature", game.players.index(player))
    extras = [
        Card("Excess one", "Creature", game.players.index(player)),
        Card("Excess two", "Creature", game.players.index(player)),
    ]
    player.hand.add_card(discarded)
    for extra in extras:
        player.hand.add_card(extra)
    assert isinstance(game.pass_turn(), TurnCleanupStepEvent)
    game.discard(player, "Discard me")
    assert isinstance(game.pass_turn(), TurnCleanupStepEvent)
    game.discard(player, "Excess one")
    game.discard(player, "Excess two")

    assert discarded in player.graveyard.get_cards()
    assert discarded not in player.hand.get_cards()
    assert len(player.hand.get_cards()) == game.maximum_hand_size


def test_discard_rejects_calls_when_hand_does_not_exceed_its_limit() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    event = game.move()
    while not isinstance(event, TurnCleanupStepEvent):
        event = game.move()

    with pytest.raises(DiscardNotRequiredError) as not_required:
        game.discard(player, "Any card")
    assert not_required.value.code == "discard_not_required"


def test_pass_turn_finishes_turn_then_stops_at_the_next_players_main_phase() -> None:
    game = game_with_opening_decks()
    first_player = game.turn.active_player
    next_player = game.players[(game.players.index(first_player) + 1) % len(game.players)]
    first_land = Card("First Forest", "Land", game.players.index(first_player))
    next_land = Card("Next Forest", "Land", game.players.index(next_player))
    first_player.hand.add_card(first_land)
    next_player.hand.add_card(next_land)

    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)
    game.play_land(first_player, first_land.name)
    event = game.pass_turn()

    assert isinstance(event, TurnPrecombatMainPhaseEvent)
    assert game.turn.active_player is next_player
    assert event.turn.active_player is next_player
    turn_events = [
        entry["type"]
        for entry in game.event_log
        if entry["type"]
        in {
            "combat_phase",
            "beginning_of_combat_step",
            "declare_attackers_step",
            "declare_blockers_step",
            "combat_damage_step",
            "end_of_combat_step",
            "second_main_phase",
            "ending_phase",
            "end_step",
            "cleanup_step",
            "beginning_phase",
            "untap_step",
            "upkeep_step",
            "draw_step",
            "first_main_phase",
        }
    ]
    assert turn_events[-15:] == [
        "combat_phase",
        "beginning_of_combat_step",
        "declare_attackers_step",
        "declare_blockers_step",
        "combat_damage_step",
        "end_of_combat_step",
        "second_main_phase",
        "ending_phase",
        "end_step",
        "cleanup_step",
        "beginning_phase",
        "untap_step",
        "upkeep_step",
        "draw_step",
        "first_main_phase",
    ]


def test_pass_uses_the_configured_maximum_hand_size() -> None:
    game = game_with_opening_decks(maximum_hand_size=8)
    player = game.turn.active_player
    next_player = game.players[(game.players.index(player) + 1) % len(game.players)]
    land = Card("Chosen Forest", "Land", game.players.index(player))
    player.hand.add_card(land)
    player.hand.add_card(Card("Keep at limit", "Creature", game.players.index(player)))
    next_player.hand.add_card(Card("Next Forest", "Land", game.players.index(next_player)))
    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)
    game.play_land(player, land.name)

    event = game.pass_turn()

    assert isinstance(event, TurnPrecombatMainPhaseEvent)
    assert game.turn.active_player is next_player


def test_pass_stops_at_the_next_players_first_main_even_without_a_land() -> None:
    game = game_with_opening_decks()
    player = game.turn.active_player
    next_player = game.players[(game.players.index(player) + 1) % len(game.players)]
    first_land = Card("First Forest", "Land", game.players.index(player))
    player.hand.add_card(first_land)
    for card in next_player.hand.get_cards():
        next_player.hand.remove_card(card)
    for card in next_player.deck.get_cards():
        next_player.deck.remove_card(card)
    for card_number in range(8):
        next_player.deck.add_card(
            Card(f"Spell {card_number}", "Instant", game.players.index(next_player))
        )

    assert isinstance(game.pass_turn(), TurnPrecombatMainPhaseEvent)
    game.play_land(player, first_land.name)
    event = game.pass_turn()

    assert isinstance(event, TurnPrecombatMainPhaseEvent)
    assert game.turn.active_player is next_player
    assert not any(card.card_type == "Land" for card in next_player.hand.get_cards())


def test_player_commands_raise_typed_errors_before_start_and_after_game_over() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    with pytest.raises(GameNotStartedError) as not_started:
        game.move()
    assert not_started.value.code == "game_not_started"

    game.start_game()
    game.result = GameResult(game.players[1], game.players[0], 1)
    with pytest.raises(GameOverError) as game_over:
        game.pass_turn()
    assert game_over.value.code == "game_over"


def test_player_commands_reject_outsiders_and_eliminated_players() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20), Player("Cara", 20)])
    for player_index, player in enumerate(game.players):
        for card_number in range(8):
            player.deck.add_card(Card(f"Land {card_number}", "Land", player_index))
    game.start_game()
    active_player = game.turn.active_player
    outsider = Player("Dora", 20)

    with pytest.raises(PlayerNotInGameError) as not_in_game:
        game.play_land(outsider, "Forest")
    assert not_in_game.value.code == "player_not_in_game"

    for card in active_player.deck.get_cards():
        active_player.deck.remove_card(card)
    active_player.draw_from_deck(1)
    with pytest.raises(PlayerEliminatedError) as eliminated:
        game.play_land(active_player, "Forest")
    assert eliminated.value.code == "player_eliminated"
