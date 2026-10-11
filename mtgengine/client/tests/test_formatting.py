"""Tests for formatting hand, state, and event responses."""

from mtgengine.client.formatting import format_event, format_game_state, format_hand


def test_hand_is_grouped_by_card_name_and_counts() -> None:
    formatted = format_hand(
        {
            "cards": [
                {"name": "Forest"},
                {"name": "Island"},
                {"name": "Forest"},
            ]
        }
    )

    assert formatted == "Forest x2\nIsland"


def test_game_state_and_events_are_human_readable() -> None:
    state = format_game_state(
        {
            "turn_number": 3,
            "active_seat": 1,
            "phase": "main",
            "step": "precombat_main",
            "players": [{"seat": 1, "name": "Bob", "life_total": 20, "hand_count": 7}],
            "battlefield": [],
            "result": None,
        }
    )

    assert "Turn 3" in state
    assert "Seat 1: Bob" in state
    assert format_event({"type": "starting_player", "data": {"seat": 1}}) == "Seat 1 goes first."
    assert format_event({"type": "land_drop", "data": {"seat": 0, "card": "Forest"}}) == (
        "Seat 0 played Forest."
    )
    assert (
        format_event(
            {
                "type": "game_over",
                "data": {
                    "winner_seat": 0,
                    "loser_seat": 1,
                    "turn_number": 54,
                    "reason": "empty_library",
                },
            }
        )
        == "Game over: Seat 0 won; Seat 1 lost on turn 54 (empty_library)."
    )
