"""Interactive prompt and background event listener for MTGTable."""

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import httpx

from mtgengine.client.commands import CommandParseError, ParsedCommand, parse_command
from mtgengine.client.formatting import format_event, format_game_state, format_hand, format_zone
from mtgengine.client.http_client import ApiError, HttpGameClient

HELP_TEXT = """Commands:
  join <spec.json>   Join with a Player Specification
  rejoin             Reconnect with this server's saved token
  list hand          Show your hand grouped by name
  list game_state    Show turn and public state
  list <zone>        Show a Zone
  play <card>        Play a land
  move               Advance one phase or step
  pass               Fast-forward to a decision point
  discard <card>     Discard during cleanup
  help               Show this text
  quit               Leave the prompt
"""


class PromptClient(Protocol):
    """HTTP operations needed by the interactive prompt."""

    def join_file(self, specification_path: str | Path) -> dict[str, object]:
        """Join using one specification file."""
        ...

    def rejoin(self) -> dict[str, object]:
        """Reconnect using a saved token."""
        ...

    def hand(self) -> dict[str, object]:
        """Read the authenticated Seat's hand."""
        ...

    def game_state(self) -> dict[str, object]:
        """Read the public game state."""
        ...

    def zone(self, name: str) -> dict[str, object]:
        """Read a named Zone."""
        ...

    def command(self, command_type: str, card: str | None = None) -> dict[str, object]:
        """Send one player command."""
        ...

    def events_after(self, after: int, wait: float) -> list[dict[str, object]]:
        """Long-poll for sequenced events."""
        ...

    def close(self) -> None:
        """Close client resources."""
        ...


class Poller(Protocol):
    """Lifecycle interface for asynchronous prompt event polling."""

    def start(self) -> None:
        """Start polling for server events."""
        ...

    def stop(self) -> None:
        """Stop the poller and wait for its worker to finish."""
        ...


class EventPoller:
    """Print sequenced events in a background thread until stopped."""

    def __init__(
        self,
        client: PromptClient,
        output: Callable[[str], None] = print,
        wait_seconds: float = 5.0,
    ) -> None:
        """Initialize an event poller.

        Args:
            client: Authenticated client used to request event batches.
            output: Thread-safe output callback for formatted events.
            wait_seconds: Long-poll duration for each request.
        """
        self.client = client
        self.output = output
        self.wait_seconds = wait_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._after = 0

    def start(self) -> None:
        """Start polling unless a poller thread is already running."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll, name="mtgtable-events", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the worker to stop and wait for its current poll to finish."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.wait_seconds + 1)

    def _poll(self) -> None:
        while not self._stop.is_set():
            try:
                events = self.client.events_after(self._after, self.wait_seconds)
            except (ApiError, httpx.HTTPError) as error:
                self.output(f"Event polling error: {error}")
                self._stop.wait(1)
                continue
            for event in events:
                sequence_value = event.get("seq")
                if not isinstance(sequence_value, int):
                    continue
                sequence = sequence_value
                if sequence > self._after:
                    self.output(format_event(event))
                    self._after = sequence


def run_play_session(
    server: str,
    join_path: str | Path | None = None,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
    client_factory: Callable[..., PromptClient] = HttpGameClient,
    event_poller_factory: Callable[..., Poller] = EventPoller,
    token_directory: Path | None = None,
) -> None:
    """Run the interactive prompt until the player enters quit or EOF.

    Args:
        server: Base URL of the MTGTable server.
        join_path: Optional Player Specification to join before prompting.
        input_fn: Prompt input function, replaceable for scripted use.
        output_fn: Output function shared with the background event poller.
        client_factory: Constructor for the HTTP client adapter.
        event_poller_factory: Constructor for the background event listener.
        token_directory: Optional directory for server-specific bearer tokens.
    """
    client = client_factory(server, token_directory=token_directory)
    try:
        InteractivePrompt(client, input_fn, output_fn, event_poller_factory).run(join_path)
    finally:
        client.close()


class InteractivePrompt:
    """Own prompt input, command routing, and poller lifecycle for one Seat."""

    def __init__(
        self,
        client: PromptClient,
        input_fn: Callable[[str], str],
        output_fn: Callable[[str], None],
        event_poller_factory: Callable[..., Poller],
    ) -> None:
        """Initialize one prompt session.

        Args:
            client: Authenticated HTTP client adapter.
            input_fn: Prompt input function.
            output_fn: Output function for prompt and event text.
            event_poller_factory: Constructor for the background poller.
        """
        self.client = client
        self.input = input_fn
        self.output = output_fn
        self.event_poller_factory = event_poller_factory
        self.poller: Poller | None = None

    def run(self, join_path: str | Path | None) -> None:
        """Run optional initial join and prompt until quit or EOF.

        Args:
            join_path: Optional Player Specification file used for initial join.
        """
        try:
            self._join_if_requested(join_path)
            while self._prompt_once():
                pass
        finally:
            self._stop_poller()

    def _join_if_requested(self, join_path: str | Path | None) -> None:
        if join_path is not None:
            self._execute(lambda: self._join(join_path))

    def _join(self, specification_path: str | Path) -> None:
        response = self.client.join_file(specification_path)
        self.output(f"Joined Seat {response['seat']}.")
        self._start_poller()

    def _prompt_once(self) -> bool:
        try:
            line = self.input("mtgtable> ")
        except EOFError:
            return False
        try:
            command = parse_command(line)
        except CommandParseError as error:
            self.output(str(error))
            return True
        if command.action == "quit":
            return False
        _run_prompt_command(command, self.client, self.output, self._start_poller)
        return True

    def _start_poller(self) -> None:
        self._stop_poller()
        self.poller = self.event_poller_factory(self.client, self.output)
        self.poller.start()

    def _stop_poller(self) -> None:
        if self.poller is not None:
            self.poller.stop()
            self.poller = None

    def _execute(self, operation: Callable[[], None]) -> None:
        try:
            operation()
        except (ApiError, OSError, TypeError, ValueError, httpx.HTTPError) as error:
            self.output(f"Error: {error}")


def _run_prompt_command(
    command: ParsedCommand,
    client: PromptClient,
    output: Callable[[str], None],
    begin_polling: Callable[[], None],
) -> None:
    try:
        if command.action == "join":
            assert command.argument is not None
            response = client.join_file(command.argument)
            output(f"Joined Seat {response['seat']}.")
            begin_polling()
        elif command.action == "rejoin":
            response = client.rejoin()
            output(f"Rejoined Seat {response['seat']}.")
            begin_polling()
        elif command.action == "list":
            _list_response(command.argument or "", client, output)
        elif command.action == "help":
            output(HELP_TEXT.rstrip())
        else:
            client.command(command.action, command.argument)
    except (ApiError, OSError, TypeError, ValueError, httpx.HTTPError) as error:
        output(f"Error: {error}")


def _list_response(zone: str, client: PromptClient, output: Callable[[str], None]) -> None:
    if zone == "hand":
        output(format_hand(client.hand()))
    elif zone == "game_state":
        output(format_game_state(client.game_state()))
    else:
        output(format_zone(client.zone(zone)))
