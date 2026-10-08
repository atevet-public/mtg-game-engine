"""Tests for Game class."""

import random

import pytest
from pyventus.events import EventLinker

from mtgengine.card import Card
from mtgengine.game import Game
from mtgengine.player import Player
from mtgengine.tests.game_test_helpers import SelectSecondPlayerRandom
from mtgengine.turn import TurnDrawStepEvent, TurnUntapStepEvent, TurnUpkeepStepEvent
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.stack import Stack


class TestGame:
    """Test suite for the Game class."""

    def test_game_initialization(self) -> None:
        """Test that a game initializes with players and a stack."""
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)
        game = Game([player1, player2])
        assert game.players == [player1, player2]
        assert isinstance(game.stack, Stack)

    def test_game_single_player(self) -> None:
        """Test that a game can be created with a single player."""
        player = Player("Solo", 20)
        game = Game([player])
        assert len(game.players) == 1
        assert game.players[0] is player

    def test_play_requires_two_players(self) -> None:
        """Reject running an MVP game with an unsupported player count."""
        game = Game([Player("Solo", 20)])

        with pytest.raises(ValueError, match="exactly two"):
            game.play()

    def test_game_requires_at_least_one_player(self) -> None:
        """Test that game raises ValueError with no players."""
        with pytest.raises(ValueError, match="at least one player"):
            Game([])

    def test_start_game_deals_hands_and_sets_current_player(self) -> None:
        """Test that start_game deals 7 cards and sets current player."""
        # Create players with 20 cards each
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)

        # Populate their decks with cards
        for i in range(20):
            card = Card(f"Card {i}", card_type="Creature", owner_index=0)
            player1.deck.add_card(card)
            card = Card(f"Card {i}", card_type="Creature", owner_index=1)
            player2.deck.add_card(card)

        game = Game([player1, player2])

        # Use a seeded RNG for deterministic testing
        rng = random.Random(42)
        game.start_game(rng=rng)

        # Each player should have 7 cards in hand
        assert len(player1.hand.get_cards()) == 7
        assert len(player2.hand.get_cards()) == 7

        # Each player should have 13 cards left in deck (20 - 7)
        assert len(player1.deck.get_cards()) == 13
        assert len(player2.deck.get_cards()) == 13

        assert game.turn.active_player in [player1, player2]

    def test_start_game_without_rng_parameter(self) -> None:
        """Test that start_game works without an explicit RNG parameter."""
        # Create players with 20 cards each
        player1 = Player("Alice", 20)
        player2 = Player("Bob", 20)

        # Populate their decks with cards
        for i in range(20):
            card = Card(f"Card {i}", card_type="Creature", owner_index=0)
            player1.deck.add_card(card)
            card = Card(f"Card {i}", card_type="Creature", owner_index=1)
            player2.deck.add_card(card)

        game = Game([player1, player2])

        # Call start_game without rng parameter (uses default)
        game.start_game()

        # Each player should have 7 cards in hand
        assert len(player1.hand.get_cards()) == 7
        assert len(player2.hand.get_cards()) == 7

        # Active player should not be none
        assert game.turn.active_player is not None


def test_start_game_sets_a_player_active() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    # preload 60 lands in each deck
    for player_index, player in enumerate(game.players):
        for _ in range(60):
            player.deck.add_card(Card("Forest", card_type="Land", owner_index=player_index))

    game.start_game()
    assert game.turn.active_player in game.players
    assert game.turn.turn_number == 1


def test_start_game_selects_and_logs_the_starting_player_before_opening_draws() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    for player_index, player in enumerate(game.players):
        for card_number in range(8):
            player.deck.add_card(
                Card(f"Player {player_index} card {card_number}", "Land", player_index)
            )

    game.start_game(SelectSecondPlayerRandom())

    assert game.turn.active_player is game.players[1]
    assert game.event_log[0] == {"type": "starting_player", "player_index": 1}
    assert game.event_log[1:3] == [
        {"type": "draw", "player_index": 0, "card": "Player 0 card 7"},
        {"type": "draw", "player_index": 0, "card": "Player 0 card 6"},
    ]
    assert game.event_log[8:10] == [
        {"type": "draw", "player_index": 1, "card": "Player 1 card 7"},
        {"type": "draw", "player_index": 1, "card": "Player 1 card 6"},
    ]
    assert len(game.event_log) == 15
    assert [len(player.hand.get_cards()) for player in game.players] == [7, 7]


def test_game_has_shared_battlefield_zone() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    assert isinstance(game.battlefield, Battlefield)


def test_game_sets_player_game_reference() -> None:
    player1 = Player("Alice", 20)
    player2 = Player("Bob", 20)
    game = Game([player1, player2])
    assert player1.game is game
    assert player2.game is game


def test_beginning_phase_steps_emit_turn_events() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    received_events: list[TurnUntapStepEvent | TurnUpkeepStepEvent | TurnDrawStepEvent] = []

    @EventLinker.on(TurnUntapStepEvent, TurnUpkeepStepEvent, TurnDrawStepEvent)
    def handle_step_event(
        event: TurnUntapStepEvent | TurnUpkeepStepEvent | TurnDrawStepEvent,
    ) -> None:
        received_events.append(event)

    game.perform_beginning_phase()

    assert [type(event) for event in received_events] == [
        TurnUntapStepEvent,
        TurnUpkeepStepEvent,
        TurnDrawStepEvent,
    ]
    assert all(event.turn.turn_number == 1 for event in received_events)
    assert all(event.turn.active_player is game.players[0] for event in received_events)


def test_game_state_flags_initialize() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    assert game.is_game_over is False
    assert game.winner is None
    assert game.event_log == []


def test_perform_untap_step_only_untaps_active_players_lands() -> None:
    """Untap only the active player's lands on the shared battlefield."""
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    active_land = Card("Forest", card_type="Land", owner_index=0)
    inactive_land = Card("Island", card_type="Land", owner_index=1)
    active_land.tap()
    inactive_land.tap()
    game.battlefield.add_card(active_land)
    game.battlefield.add_card(inactive_land)

    game.perform_untap_step()

    assert active_land.tapped is False
    assert inactive_land.tapped is True


def test_perform_upkeep_step_logs_event() -> None:
    """Log the active player's upkeep step."""
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    game.perform_upkeep_step()

    assert game.event_log[-1] == {"type": "upkeep_step", "player_index": 0}


def test_draw_card_from_deck_moves_top_card_to_hand() -> None:
    """Draw the active player's top deck card into their hand."""
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    card = Card("Forest", card_type="Land", owner_index=0)
    game.turn.active_player.deck.add_card(card)

    drawn_card = game.draw_card_from_deck()

    assert drawn_card is card
    assert card in game.turn.active_player.hand.get_cards()
    assert card not in game.turn.active_player.deck.get_cards()


def test_draw_card_from_deck_returns_none_if_deck_empty() -> None:
    """Return None if the active player's deck is empty."""
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    drawn_card = game.draw_card_from_deck()

    assert drawn_card is None


def test_perform_draw_step_draws_card_from_deck() -> None:
    """Performing the draw step should draw a card from the active player's deck."""
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    card = Card("Forest", card_type="Land", owner_index=0)
    game.turn.active_player.deck.add_card(card)

    game.perform_draw_step()

    assert card in game.turn.active_player.hand.get_cards()
    assert card not in game.turn.active_player.deck.get_cards()


def test_starting_player_skips_their_first_draw_step_only() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    for player_index, player in enumerate(game.players):
        for card_number in range(9):
            player.deck.add_card(
                Card(f"Player {player_index} card {card_number}", "Land", player_index)
            )
    game.start_game(SelectSecondPlayerRandom())
    starting_hand_size = len(game.players[1].hand.get_cards())

    game.perform_draw_step()

    assert len(game.players[1].hand.get_cards()) == starting_hand_size
    assert len(game.players[0].hand.get_cards()) == 7
    assert game.event_log[-1] == {"type": "draw", "player_index": 1, "card": "Player 1 card 2"}

    game.advance_to_next_player()
    game.advance_to_next_player()
    game.perform_draw_step()
    assert len(game.players[1].hand.get_cards()) == starting_hand_size + 1
    assert game.event_log[-1] == {"type": "draw", "player_index": 1, "card": "Player 1 card 1"}


def test_successfully_drawing_last_card_does_not_end_game() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    last_card = Card("Forest", "Land", 0)
    game.players[0].deck.add_card(last_card)

    game.perform_draw_step()

    assert game.players[0].hand.get_cards() == [last_card]
    assert game.check_for_empty_deck_loss() is False
    assert game.is_game_over is False


def test_empty_deck_does_not_cause_loss_until_a_draw_is_attempted() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    assert game.check_for_empty_deck_loss() is False
    assert game.is_game_over is False


def test_failed_draw_by_another_player_does_not_end_active_players_game() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    assert game.draw_card_from_deck(game.players[1]) is None
    assert game.check_for_empty_deck_loss() is False
    assert game.is_game_over is False


def test_failed_draw_marker_expires_after_the_turn_cycle() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    assert game.draw_card_from_deck(game.players[0]) is None
    game.advance_to_next_player()
    game.advance_to_next_player()

    assert game.check_for_empty_deck_loss() is False
    assert game.is_game_over is False


def test_failed_draw_from_empty_deck_ends_game_for_active_player() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])

    game.perform_draw_step()

    assert game.is_game_over is True
    assert game.winner is game.players[1]
    assert game.event_log == [{"type": "game_over", "player_index": 0, "reason": "empty_library"}]


def test_draw_step_does_not_mutate_other_games() -> None:
    first_game = Game([Player("Alice", 20), Player("Bob", 20)])
    second_game = Game([Player("Cara", 20), Player("Dan", 20)])
    card = Card("Forest", "Land", 0)
    second_game.players[0].deck.add_card(card)

    second_game.perform_draw_step()

    assert first_game.event_log == []
    assert second_game.players[0].hand.get_cards() == [card]
    assert second_game.event_log == [{"type": "draw", "player_index": 0, "card": "Forest"}]


def test_first_main_phase_plays_a_land_from_the_active_players_hand() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    land = Card("Forest", "Land", 0)
    land.tap()
    game.players[0].hand.add_card(land)

    game.perform_first_main_phase()

    assert game.players[0].hand.get_cards() == []
    assert game.battlefield.get_cards() == [land]
    assert land.owner_index == 0
    assert land.tapped is False
    assert game.event_log[-1] == {"type": "land_drop", "player_index": 0, "card": "Forest"}
    assert game.event_log[-2] == {"type": "first_main_phase", "player_index": 0}


def test_player_can_make_only_one_land_drop_per_turn() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    first_land = Card("Forest", "Land", 0)
    second_land = Card("Island", "Land", 0)
    game.players[0].hand.add_card(first_land)
    game.players[0].hand.add_card(second_land)

    assert game.perform_play_land() is True
    assert game.perform_play_land() is False

    assert game.battlefield.get_cards() == [first_land]
    assert game.players[0].hand.get_cards() == [second_land]


def test_first_main_phase_does_not_play_nonland_cards() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    spell = Card("Lightning Bolt", "Instant", 0)
    game.players[0].hand.add_card(spell)

    game.perform_first_main_phase()

    assert game.players[0].hand.get_cards() == [spell]
    assert game.battlefield.get_cards() == []
    assert game.event_log == [{"type": "first_main_phase", "player_index": 0}]


def test_later_turn_phases_emit_events_and_cleanup_discards_to_seven() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    for card_number in range(9):
        game.players[0].hand.add_card(Card(f"Card {card_number}", "Land", 0))

    game.perform_combat_phase()
    game.perform_second_main_phase()
    game.perform_cleanup_step()

    assert len(game.players[0].hand.get_cards()) == 7
    assert [card.name for card in game.players[0].graveyard.get_cards()] == ["Card 0", "Card 1"]
    assert game.event_log[-2:] == [
        {"type": "discard", "player_index": 0, "card": "Card 0"},
        {"type": "discard", "player_index": 0, "card": "Card 1"},
    ]
    assert {event["type"] for event in game.event_log} >= {
        "combat_phase",
        "second_main_phase",
    }


def test_turn_does_not_continue_to_cleanup_after_empty_library_loss() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    game.players[0].hand.add_card(Card("Keep this card", "Land", 0))

    game.perform_beginning_phase()
    game.perform_first_main_phase()
    game.perform_combat_phase()
    game.perform_second_main_phase()
    game.perform_cleanup_step()

    assert game.is_game_over is True
    assert game.players[0].hand.get_cards()[0].name == "Keep this card"


def test_turn_number_increments_only_after_both_players_complete_a_cycle() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    for player_index, player in enumerate(game.players):
        for card_number in range(10):
            player.deck.add_card(
                Card(f"Player {player_index} card {card_number}", "Land", player_index)
            )
    game.start_game(SelectSecondPlayerRandom())

    game.advance_to_next_player()
    assert game.turn.active_player is game.players[0]
    assert game.turn.turn_number == 1

    game.advance_to_next_player()
    assert game.turn.active_player is game.players[1]
    assert game.turn.turn_number == 2


def test_land_drop_availability_resets_when_turn_advances() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    first_land = Card("Forest", "Land", 0)
    next_land = Card("Island", "Land", 0)
    game.players[0].hand.add_card(first_land)
    game.players[0].hand.add_card(next_land)

    game.perform_play_land()
    game.advance_to_next_player()
    game.advance_to_next_player()

    assert game.perform_play_land() is True
    assert game.battlefield.get_cards() == [first_land, next_land]
