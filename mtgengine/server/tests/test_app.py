"""HTTP contract tests for MTGTable's server core."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from mtgengine.card import Card
from mtgengine.game_result import GameResult
from mtgengine.server import cli
from mtgengine.server.app import create_app


def player_specification(name: str, starting_life: int = 20) -> dict[str, object]:
    return {"name": name, "decklist": "60 Forest", "starting_life": starting_life}


def join(client: TestClient, name: str, starting_life: int = 20) -> dict[str, object]:
    response = client.post("/join", json=player_specification(name, starting_life))
    assert response.status_code == 200
    return response.json()


def test_invalid_specification_does_not_claim_a_seat() -> None:
    with TestClient(create_app()) as client:
        invalid = client.post("/join", json={"name": "Alice", "decklist": "59 Forest"})

        assert invalid.status_code == 422
        assert "at least 60" in invalid.json()["detail"]["message"]
        assert join(client, "Alice")["seat"] == 0


def test_join_rejects_duplicate_names_and_full_lobbies() -> None:
    with TestClient(create_app()) as client:
        first_seat = join(client, "Alice")
        duplicate = client.post("/join", json=player_specification(" alice "))
        second_seat = join(client, "Bob")
        full = client.post("/join", json=player_specification("Cara"))

        assert first_seat["seat"] == 0
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "name_taken"
        assert second_seat["seat"] == 1
        assert full.status_code == 409
        assert full.json()["detail"]["code"] == "game_full"


def test_join_starts_game_and_sequences_lobby_events() -> None:
    app = create_app()
    with TestClient(app) as client:
        first = join(client, "Alice")
        assert app.state.lobby.game is None
        second = join(client, "Bob", starting_life=30)

        assert second["seat"] == 1
        assert second["token_type"] == "bearer"
        assert app.state.lobby.game is not None
        assert all(len(player.hand.get_cards()) == 7 for player in app.state.lobby.game.players)
        assert app.state.lobby.game.players[1].life_total == 30
        assert [event.type for event in app.state.lobby.events[:1]] == ["game_started"]
        assert app.state.lobby.events[-1].type == "hands_dealt"
        assert first["token"] != second["token"]


def test_authenticated_queries_return_public_state_and_only_own_hand() -> None:
    app = create_app()
    with TestClient(app) as client:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        headers = {"Authorization": f"Bearer {alice['token']}"}
        game = app.state.lobby.game
        assert game is not None
        game.battlefield.add_card(Card("Borrowed Forest", "Land", 0, controller_index=1))
        game.move()
        game.move()

        game_state = client.get("/game", headers=headers)
        hand = client.get("/players/me/hand", headers=headers)
        private_zone = client.get("/zones/hand?seat=1", headers=headers)
        graveyard = client.get("/zones/graveyard", headers=headers)

        assert game_state.status_code == 200
        assert {player["seat"] for player in game_state.json()["players"]} == {0, 1}
        assert game_state.json()["turn_number"] == 1
        assert game_state.json()["phase"] == "beginning"
        assert game_state.json()["step"] == "untap_step"
        assert game_state.json()["battlefield"][0]["owner_seat"] == 0
        assert game_state.json()["battlefield"][0]["controller_seat"] == 1
        assert len(hand.json()["cards"]) == 7
        assert hand.json()["seat"] == 0
        assert private_zone.status_code == 403
        assert private_zone.json()["detail"]["code"] == "forbidden_seat"
        assert graveyard.status_code == 200
        assert bob["seat"] == 1


def test_player_queries_require_a_valid_bearer_token() -> None:
    with TestClient(create_app()) as client:
        missing = client.get("/game")
        invalid = client.get("/players/me/hand", headers={"Authorization": "Bearer invalid"})

        assert missing.status_code == invalid.status_code == 401
        assert missing.json()["detail"]["code"] == "unauthorized"


def test_persistent_bearer_token_reconnects_to_the_same_seat() -> None:
    with TestClient(create_app()) as client:
        alice = join(client, "Alice")
        join(client, "Bob")
        headers = {"Authorization": f"Bearer {alice['token']}"}

        rejoined_hand = client.get("/players/me/hand", headers=headers)
        game = client.get("/game", headers=headers)
        rejoined_seat = client.get("/rejoin", headers=headers)

        assert rejoined_hand.status_code == 200
        assert rejoined_hand.json()["seat"] == alice["seat"]
        assert rejoined_seat.json()["seat"] == alice["seat"]
        assert {player["seat"] for player in game.json()["players"]} == {0, 1}


def test_malformed_command_uses_machine_readable_validation_error() -> None:
    with TestClient(create_app()) as client:
        alice = join(client, "Alice")
        invalid = client.post(
            "/commands",
            json={"type": "shuffle"},
            headers={"Authorization": f"Bearer {alice['token']}"},
        )

        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "invalid_request"
        assert invalid.json()["detail"]["message"]


def test_zone_and_server_configuration_validation() -> None:
    with pytest.raises(ValueError, match="only two"):
        create_app(expected_players=3)

    with TestClient(create_app()) as client:
        player = join(client, "Alice")
        join(client, "Bob")
        unknown_zone = client.get(
            "/zones/unknown", headers={"Authorization": f"Bearer {player['token']}"}
        )
        assert unknown_zone.status_code == 404
        assert unknown_zone.json()["detail"]["code"] == "zone_not_found"


def test_serve_cli_forwards_server_options_and_uses_one_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: dict[str, object] = {}

    def record_run(app: object, **options: object) -> None:
        received.update(app=app, **options)

    monkeypatch.setattr(cli.uvicorn, "run", record_run)

    cli.main(["serve", "--players", "2", "--host", "0.0.0.0", "--port", "9000"])

    assert received["host"] == "0.0.0.0"
    assert received["port"] == 9000
    assert received["workers"] == 1


def test_serve_cli_rejects_player_counts_other_than_two() -> None:
    with pytest.raises(SystemExit):
        cli.main(["serve", "--players", "3"])


def test_commands_enforce_active_seat_and_preserve_pass_events() -> None:
    with TestClient(create_app()) as client:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        alice_headers = {"Authorization": f"Bearer {alice['token']}"}
        bob_headers = {"Authorization": f"Bearer {bob['token']}"}
        active_seat = client.get("/game", headers=alice_headers).json()["active_seat"]
        active_headers, inactive_headers = (
            (alice_headers, bob_headers) if active_seat == 0 else (bob_headers, alice_headers)
        )

        rejected = client.post("/commands", json={"type": "move"}, headers=inactive_headers)
        passed = client.post("/commands", json={"type": "pass"}, headers=active_headers)
        state = client.get("/game", headers=active_headers)
        played = client.post(
            "/commands", json={"type": "play", "card": "fOrEsT"}, headers=active_headers
        )

        assert rejected.status_code == 409
        assert rejected.json()["detail"]["code"] == "not_your_turn"
        assert passed.status_code == 200
        assert [event["type"] for event in passed.json()["events"]] == [
            "beginning_phase",
            "untap_step",
            "upkeep_step",
            "draw_step",
            "first_main_phase",
        ]
        assert state.json()["phase"] == "main"
        assert played.status_code == 200
        assert played.json()["events"][-1]["type"] == "land_drop"


def test_discard_command_waits_for_cleanup_and_moves_card_to_graveyard() -> None:
    app = create_app()
    with TestClient(app) as client:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        headers_by_seat = [
            {"Authorization": f"Bearer {alice['token']}"},
            {"Authorization": f"Bearer {bob['token']}"},
        ]
        active_seat = client.get("/game", headers=headers_by_seat[0]).json()["active_seat"]
        headers = headers_by_seat[active_seat]
        game = app.state.lobby.game
        assert game is not None
        active_player = game.players[active_seat]

        client.post("/commands", json={"type": "pass"}, headers=headers)
        client.post("/commands", json={"type": "play", "card": "Forest"}, headers=headers)
        wrong_phase = client.post(
            "/commands", json={"type": "discard", "card": "Filler A"}, headers=headers
        )
        for name in ("Filler A", "Filler B"):
            active_player.hand.add_card(Card(name, "Instant", active_seat))
        passed = client.post("/commands", json={"type": "pass"}, headers=headers)
        missing_card = client.post(
            "/commands", json={"type": "discard", "card": "Missing"}, headers=headers
        )
        discarded = client.post(
            "/commands", json={"type": "discard", "card": "filler a"}, headers=headers
        )

        assert "cleanup_step" in [event["type"] for event in passed.json()["events"]]
        assert wrong_phase.status_code == 422
        assert wrong_phase.json()["detail"]["code"] == "wrong_phase"
        assert missing_card.status_code == 422
        assert missing_card.json()["detail"]["code"] == "card_not_in_hand"
        assert discarded.status_code == 200
        assert discarded.json()["events"][-1]["type"] == "discard"
        assert any(card.name == "Filler A" for card in active_player.graveyard.get_cards())


def test_play_command_rejects_missing_nonland_and_second_land_drop() -> None:
    app = create_app()
    with TestClient(app) as client:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        headers_by_seat = [
            {"Authorization": f"Bearer {alice['token']}"},
            {"Authorization": f"Bearer {bob['token']}"},
        ]
        active_seat = client.get("/game", headers=headers_by_seat[0]).json()["active_seat"]
        headers = headers_by_seat[active_seat]
        game = app.state.lobby.game
        assert game is not None
        game.players[active_seat].hand.add_card(Card("Bolt", "Instant", active_seat))

        missing_name = client.post("/commands", json={"type": "play"}, headers=headers)
        wrong_phase = client.post(
            "/commands", json={"type": "play", "card": "Forest"}, headers=headers
        )
        client.post("/commands", json={"type": "pass"}, headers=headers)
        absent = client.post("/commands", json={"type": "play", "card": "Absent"}, headers=headers)
        nonland = client.post("/commands", json={"type": "play", "card": "Bolt"}, headers=headers)
        client.post("/commands", json={"type": "play", "card": "Forest"}, headers=headers)
        second_drop = client.post(
            "/commands", json={"type": "play", "card": "Forest"}, headers=headers
        )

        assert missing_name.status_code == 422
        assert missing_name.json()["detail"]["code"] == "missing_card"
        assert wrong_phase.status_code == 422
        assert wrong_phase.json()["detail"]["code"] == "wrong_phase"
        assert absent.status_code == 422
        assert absent.json()["detail"]["code"] == "card_not_in_hand"
        assert nonland.status_code == 422
        assert nonland.json()["detail"]["code"] == "not_a_land"
        assert second_drop.status_code == 422
        assert second_drop.json()["detail"]["code"] == "no_land_drop_left"


def test_event_poll_redacts_other_players_draws_and_wakes_for_new_events() -> None:
    with TestClient(create_app()) as client, ThreadPoolExecutor() as executor:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        headers_by_seat = [
            {"Authorization": f"Bearer {alice['token']}"},
            {"Authorization": f"Bearer {bob['token']}"},
        ]
        active_seat = client.get("/game", headers=headers_by_seat[0]).json()["active_seat"]
        alice_events = client.get("/events?after=0&wait=0", headers=headers_by_seat[0]).json()[
            "events"
        ]
        draw_events = [event for event in alice_events if event["type"] == "draw"]

        assert all("card" in event["data"] for event in draw_events if event["data"]["seat"] == 0)
        assert all(
            "card" not in event["data"] for event in draw_events if event["data"]["seat"] == 1
        )
        next_sequence = alice_events[-1]["seq"]
        poll = executor.submit(
            client.get,
            f"/events?after={next_sequence}&wait=1",
            headers=headers_by_seat[active_seat],
        )
        command = client.post(
            "/commands", json={"type": "move"}, headers=headers_by_seat[active_seat]
        )
        arrived = poll.result(timeout=2)

        assert command.status_code == 200
        assert arrived.status_code == 200
        assert arrived.json()["events"]
        assert arrived.json()["events"][0]["seq"] > next_sequence


def test_game_over_rejects_commands_but_state_queries_still_work() -> None:
    app = create_app()
    with TestClient(app) as client:
        alice = join(client, "Alice")
        bob = join(client, "Bob")
        game = app.state.lobby.game
        assert game is not None
        game.result = GameResult(game.players[0], game.players[1], 1)
        headers = {"Authorization": f"Bearer {alice['token']}"}

        commands = [
            client.post("/commands", json={"type": command_type, "card": "Forest"}, headers=headers)
            for command_type in ("play", "move", "pass", "discard")
        ]
        state = client.get("/game", headers=headers)

        assert all(command.status_code == 409 for command in commands)
        assert all(command.json()["detail"]["code"] == "game_over" for command in commands)
        assert state.status_code == 200
        assert state.json()["result"]["winner_seat"] == 0
        assert bob["seat"] == 1
