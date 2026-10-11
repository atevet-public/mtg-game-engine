"""Synchronous HTTP client and per-server bearer-token storage."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx


class ApiError(Exception):
    """HTTP error with the server's machine-readable code."""

    status_code: int
    code: str

    def __init__(self, status_code: int, code: str, message: str) -> None:
        """Initialize an API failure.

        Args:
            status_code: HTTP response status.
            code: Machine-readable server error code.
            message: Human-readable server explanation.
        """
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def token_file_for_server(server: str, directory: Path | None = None) -> Path:
    """Return the token file path for a server URL.

    Args:
        server: Base URL of the MTGTable server.
        directory: Optional token directory, otherwise ``~/.mtg-cli``.

    Returns:
        A path whose filename safely encodes the server URL.
    """
    token_directory = directory or Path.home() / ".mtg-cli"
    encoded_server = quote(server.rstrip("/"), safe="")
    return token_directory / f"{encoded_server}.token"


class HttpGameClient:
    """HTTPX adapter for the join, query, command, and event APIs."""

    def __init__(
        self,
        server: str,
        token_directory: Path | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize an HTTP client for one server.

        Args:
            server: Base URL of the MTGTable server.
            token_directory: Optional directory for the saved bearer token.
            transport: Optional HTTPX transport for tests or custom deployments.
        """
        self.server = server.rstrip("/")
        self.token_file = token_file_for_server(self.server, token_directory)
        self.http = httpx.Client(base_url=self.server, timeout=35, transport=transport)
        self.token: str | None = None
        self.seat: int | None = None

    def join_file(self, specification_path: str | Path) -> dict[str, Any]:
        """Read a Player Specification JSON file, join, and persist its token.

        Args:
            specification_path: JSON file containing name, decklist, and optional starting_life.

        Returns:
            Join response containing the assigned Seat and token type.
        """
        specification = json.loads(Path(specification_path).read_text(encoding="utf-8"))
        if not isinstance(specification, dict):
            raise TypeError("The Player Specification file must contain a JSON object")
        response = self._request("POST", "/join", json=specification, authenticated=False)
        self.token = str(response["token"])
        self.seat = int(response["seat"])
        self.token_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.token_file.write_text(self.token, encoding="utf-8")
        self.token_file.chmod(0o600)
        return response

    def rejoin(self) -> dict[str, Any]:
        """Load this server's saved token and resolve its existing Seat.

        Returns:
            Rejoined Seat information.

        Raises:
            ValueError: If no token file exists for this server.
            ApiError: If the saved token is no longer valid.
        """
        if not self.token_file.exists():
            raise ValueError(f"No saved token for {self.server}")
        self.token = self.token_file.read_text(encoding="utf-8").strip()
        response = self._request("GET", "/rejoin")
        self.seat = int(response["seat"])
        return response

    def game_state(self) -> dict[str, Any]:
        """Fetch the public game state."""
        return self._request("GET", "/game")

    def hand(self) -> dict[str, Any]:
        """Fetch this token's private hand."""
        return self._request("GET", "/players/me/hand")

    def zone(self, name: str) -> dict[str, Any]:
        """Fetch a visible game Zone by name.

        Args:
            name: Zone name such as battlefield, graveyard, or hand.

        Returns:
            Zone response data.
        """
        return self._request("GET", f"/zones/{name}")

    def command(self, command_type: str, card: str | None = None) -> dict[str, Any]:
        """Send one player command.

        Args:
            command_type: One of play, move, pass, or discard.
            card: Card name for play and discard commands.

        Returns:
            Sequenced event data produced by the command.
        """
        payload: dict[str, object] = {"type": command_type}
        if card is not None:
            payload["card"] = card
        return self._request("POST", "/commands", json=payload)

    def events_after(self, after: int, wait: float) -> list[dict[str, Any]]:
        """Long-poll for sequenced events after a cursor.

        Args:
            after: Last event sequence already received.
            wait: Maximum seconds to wait for a new event.

        Returns:
            Events after the supplied sequence, redacted for this Seat.
        """
        response = self._request("GET", "/events", params={"after": after, "wait": wait})
        return response["events"]

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, object] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._require_token()}"} if authenticated else {}
        response = self.http.request(method, path, json=json, params=params, headers=headers)
        payload = response.json()
        if not response.is_success:
            detail = payload.get("detail", {}) if isinstance(payload, dict) else {}
            code = detail.get("code", "http_error") if isinstance(detail, dict) else "http_error"
            message = (
                detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail)
            )
            raise ApiError(response.status_code, str(code), str(message))
        return payload

    def _require_token(self) -> str:
        if self.token is None:
            raise ApiError(401, "unauthorized", "Join or rejoin before using this command")
        return self.token

    def close(self) -> None:
        """Close the underlying HTTPX connection pool."""
        self.http.close()
