"""Tests for the scripted interactive prompt."""

from collections.abc import Callable
from pathlib import Path
from threading import Event

from mtgengine.client.session import EventPoller, run_play_session


class FakeClient:
    def __init__(self, _server: str, **_options: object) -> None:
        self.actions: list[tuple[str, str | None]] = []
        self.joined: list[str] = []
        self.closed = False

    def join_file(self, path: str | Path) -> dict[str, object]:
        self.joined.append(str(path))
        return {"seat": 0}

    def rejoin(self) -> dict[str, object]:
        return {"seat": 0}

    def hand(self) -> dict[str, object]:
        return {"cards": [{"name": "Forest"}, {"name": "Forest"}]}

    def game_state(self) -> dict[str, object]:
        return {
            "turn_number": 1,
            "active_seat": 0,
            "phase": "main",
            "step": "precombat_main",
            "players": [],
            "battlefield": [],
            "result": None,
        }

    def zone(self, name: str) -> dict[str, object]:
        return {"zone": name, "cards": []}

    def command(self, command_type: str, card: str | None = None) -> dict[str, object]:
        self.actions.append((command_type, card))
        return {"events": []}

    def events_after(self, _after: int, _wait: float) -> list[dict[str, object]]:
        return []

    def close(self) -> None:
        self.closed = True


class FakePoller:
    def __init__(self, _client: FakeClient, _output: Callable[[str], None]) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_prompt_routes_commands_lists_and_closes_background_polling() -> None:
    client = FakeClient("http://table.test")
    poller: FakePoller | None = None
    output: list[str] = []
    lines = iter(
        [
            "list hand",
            "list game_state",
            "play Forest",
            "move",
            "pass",
            "discard Island",
            "help",
            "quit",
        ]
    )

    def poller_factory(fake_client: FakeClient, writer: Callable[[str], None]) -> FakePoller:
        nonlocal poller
        poller = FakePoller(fake_client, writer)
        return poller

    run_play_session(
        "http://table.test",
        input_fn=lambda _prompt: next(lines),
        output_fn=output.append,
        client_factory=lambda *_args, **_options: client,
        event_poller_factory=poller_factory,
    )

    assert "Forest x2" in output
    assert any("Turn 1" in line for line in output)
    assert client.actions == [
        ("play", "Forest"),
        ("move", None),
        ("pass", None),
        ("discard", "Island"),
    ]
    assert client.closed
    assert poller is None


def test_initial_join_starts_poller_and_prompt_rejoin_resolves_saved_seat() -> None:
    client = FakeClient("http://table.test")
    pollers: list[FakePoller] = []
    output: list[str] = []
    lines = iter(["rejoin", "quit"])

    def poller_factory(fake_client: FakeClient, writer: Callable[[str], None]) -> FakePoller:
        poller = FakePoller(fake_client, writer)
        pollers.append(poller)
        return poller

    run_play_session(
        "http://table.test",
        join_path="players/alice.json",
        input_fn=lambda _prompt: next(lines),
        output_fn=output.append,
        client_factory=lambda *_args, **_options: client,
        event_poller_factory=poller_factory,
    )

    assert client.joined == ["players/alice.json"]
    assert len(pollers) == 2
    assert all(poller.started and poller.stopped for poller in pollers)
    assert "Rejoined Seat 0." in output


def test_event_poller_prints_formatted_events_from_the_background_thread() -> None:
    received = Event()
    output: list[str] = []

    class PollingClient(FakeClient):
        returned = False

        def events_after(self, _after: int, _wait: float) -> list[dict[str, object]]:
            if self.returned:
                received.wait(0.01)
                return []
            self.returned = True
            return [{"seq": 1, "type": "starting_player", "data": {"seat": 1}}]

    def write(message: str) -> None:
        output.append(message)
        received.set()

    poller = EventPoller(PollingClient("http://table.test"), write, wait_seconds=0.01)
    poller.start()
    assert received.wait(1)
    poller.stop()

    assert output == ["Seat 1 goes first."]
