"""HTTP contract tests for MTGTable's server core."""

import pytest
from fastapi.testclient import TestClient

from mtgengine.card import Card
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
