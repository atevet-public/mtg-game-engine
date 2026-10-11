"""Subprocess integration test for two-seat MTGTable games."""

import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Event
from typing import Any, cast

import httpx
import pytest

pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(client: httpx.Client, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"mtgtable serve exited with status {process.returncode}")
        try:
            if client.get("/openapi.json").status_code == 200:
                return
        except httpx.ConnectError:
            Event().wait(0.05)
    pytest.fail("mtgtable server did not become ready")


def _authorized(client: httpx.Client, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _read_game_state(client: httpx.Client, token: str) -> dict[str, Any]:
    response = client.get("/game", headers=_authorized(client, token))
    assert response.status_code == 200
    return response.json()


def _pass_to_main_phase(
    clients: list[httpx.Client], tokens: list[str], state: dict[str, Any]
) -> dict[str, Any]:
    while state["phase"] != "main":
        seat = state["active_seat"]
        response = clients[seat].post(
            "/commands", json={"type": "pass"}, headers=_authorized(clients[seat], tokens[seat])
        )
        assert response.status_code == 200
        state = _read_game_state(clients[0], tokens[0])
        if state["result"] is not None:
            return state
    return state


def _play_land_and_pass(clients: list[httpx.Client], tokens: list[str], seat: int) -> None:
    card = "Forest" if seat == 0 else "Island"
    client = clients[seat]
    headers = _authorized(client, tokens[seat])
    for command in ({"type": "play", "card": card}, {"type": "pass"}):
        response = client.post("/commands", json=command, headers=headers)
        assert response.status_code == 200


def _advance_to_game_over(clients: list[httpx.Client], tokens: list[str]) -> dict[str, Any]:
    state = _read_game_state(clients[0], tokens[0])
    for _ in range(110):
        if state["result"] is not None:
            return state
        state = _pass_to_main_phase(clients, tokens, state)
        if state["result"] is not None:
            return state
        _play_land_and_pass(clients, tokens, state["active_seat"])
        state = _read_game_state(clients[0], tokens[0])
    pytest.fail("lands-only game did not reach game over")


@contextmanager
def _running_server() -> Iterator[tuple[subprocess.Popen[bytes], str]]:
    executable = shutil.which("mtgtable") or str(Path(sys.executable).with_name("mtgtable"))
    if not os.path.isfile(executable):
        pytest.fail("Install the project with make deps before running integration tests")
    port = _free_port()
    process = subprocess.Popen(
        [executable, "serve", "--players", "2", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        yield process, base_url
    finally:
        _stop_server(process)


def _stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _join_players(alice: httpx.Client, bob: httpx.Client) -> tuple[list[httpx.Client], list[str]]:
    first = alice.post("/join", json={"name": "Alice", "decklist": "60 Forest"})
    second = bob.post("/join", json={"name": "Bob", "decklist": "60 Island"})
    assert first.status_code == second.status_code == 200
    return [alice, bob], [first.json()["token"], second.json()["token"]]


def _assert_setup_events(client: httpx.Client, token: str) -> None:
    events = client.get("/events?after=0&wait=0", headers=_authorized(client, token)).json()[
        "events"
    ]
    assert events[0]["type"] == "game_started"
    assert events[-1]["type"] == "hands_dealt"


def _assert_game_over_events(client: httpx.Client, token: str, state: dict[str, Any]) -> None:
    result = cast(dict[str, Any], state["result"])
    assert result["reason"] == "empty_library"
    assert result["winner_seat"] in (0, 1)
    assert result["loser_seat"] in (0, 1)
    assert result["winner_seat"] != result["loser_seat"]
    events = client.get("/events?after=0&wait=0", headers=_authorized(client, token)).json()[
        "events"
    ]
    assert any(event["type"] == "land_drop" for event in events)
    assert any(event["type"] == "game_over" for event in events)


def test_two_http_clients_play_lands_only_game_to_game_over() -> None:
    with (
        _running_server() as (process, base_url),
        httpx.Client(base_url=base_url, timeout=10) as alice,
        httpx.Client(base_url=base_url, timeout=10) as bob,
    ):
        _wait_for_server(alice, process)
        clients, tokens = _join_players(alice, bob)
        _assert_setup_events(alice, tokens[0])
        state = _advance_to_game_over(clients, tokens)
        _assert_game_over_events(alice, tokens[0], state)
