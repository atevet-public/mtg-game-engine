"""Tests for HTTP requests and per-server token persistence."""

import json
from pathlib import Path
from stat import S_IMODE

import httpx
import pytest

from mtgengine.client.http_client import ApiError, HttpGameClient, token_file_for_server


def test_token_path_is_scoped_to_server(tmp_path: Path) -> None:
    token_path = token_file_for_server("http://127.0.0.1:8000", tmp_path)

    assert token_path.parent == tmp_path
    assert token_path.name.endswith(".token")
    assert "/" not in token_path.name


def test_join_persists_token_and_rejoin_resolves_same_seat(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/join":
            assert json.loads(request.content) == {"name": "Alice", "decklist": "60 Forest"}
            return httpx.Response(
                200, json={"seat": 0, "token": "opaque-token", "token_type": "bearer"}
            )
        assert request.url.path == "/rejoin"
        assert request.headers["Authorization"] == "Bearer opaque-token"
        return httpx.Response(200, json={"seat": 0, "name": "Alice"})

    specification = tmp_path / "alice.json"
    specification.write_text(json.dumps({"name": "Alice", "decklist": "60 Forest"}))
    client = HttpGameClient(
        "http://table.test",
        token_directory=tmp_path / ".tokens",
        transport=httpx.MockTransport(respond),
    )

    joined = client.join_file(specification)
    client.token = None
    rejoined = client.rejoin()

    assert joined["seat"] == rejoined["seat"] == 0
    assert client.token_file.read_text() == "opaque-token"
    assert S_IMODE(client.token_file.stat().st_mode) == 0o600
    assert len(requests) == 2
    client.close()


def test_queries_commands_and_events_use_the_saved_bearer_token(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer seat-token"
        if request.url.path == "/events":
            return httpx.Response(200, json={"events": [{"seq": 2, "type": "move", "data": {}}]})
        if request.url.path == "/commands":
            assert json.loads(request.content) == {"type": "play", "card": "Forest"}
            return httpx.Response(200, json={"events": []})
        return httpx.Response(200, json={"cards": []})

    client = HttpGameClient(
        "http://table.test",
        token_directory=tmp_path,
        transport=httpx.MockTransport(respond),
    )
    client.token = "seat-token"

    client.game_state()
    client.hand()
    client.zone("graveyard")
    client.command("play", "Forest")
    events = client.events_after(1, 0.1)

    assert events == [{"seq": 2, "type": "move", "data": {}}]
    assert [request.url.path for request in requests] == [
        "/game",
        "/players/me/hand",
        "/zones/graveyard",
        "/commands",
        "/events",
    ]
    client.close()


def test_http_errors_preserve_machine_readable_details() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={"detail": {"code": "wrong_phase", "message": "Not a main phase"}},
        )

    client = HttpGameClient("http://table.test", transport=httpx.MockTransport(respond))
    client.token = "seat-token"

    with pytest.raises(ApiError) as failure:
        client.command("play", "Forest")
    assert failure.value.code == "wrong_phase"
    assert str(failure.value) == "Not a main phase"
    client.close()
