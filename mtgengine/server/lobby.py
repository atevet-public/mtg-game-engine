"""Seat management, game lifecycle, event sequencing, and safe state projections."""

import asyncio
import random
import secrets
from dataclasses import dataclass

from mtgengine import decklist_validator
from mtgengine.action_errors import GameActionError
from mtgengine.card import Card
from mtgengine.decklist import parse_decklist
from mtgengine.game import Game
from mtgengine.game_result import GameResult
from mtgengine.player import Player
from mtgengine.player_specification import PlayerSpecification
from mtgengine.server.api_models import (
    CardResponse,
    EventResponse,
    EventsResponse,
    GameResponse,
    GameResultResponse,
    HandResponse,
    JoinResponse,
    PlayerResponse,
    SeatResponse,
    ZoneResponse,
)
from mtgengine.turn import Turn, TurnEvent

_ZONE_NAMES = {"battlefield", "graveyard", "exile", "stack", "hand", "deck"}
_PHASE_BY_EVENT_NAME = {
    "beginning_phase": "beginning",
    "untap_step": "beginning",
    "upkeep_step": "beginning",
    "draw_step": "beginning",
    "first_main_phase": "main",
    "combat_phase": "combat",
    "beginning_of_combat_step": "combat",
    "declare_attackers_step": "combat",
    "declare_blockers_step": "combat",
    "combat_damage_step": "combat",
    "end_of_combat_step": "combat",
    "second_main_phase": "main",
    "ending_phase": "ending",
    "end_step": "ending",
    "cleanup_step": "ending",
}
_PHASE_EVENT_NAMES = {
    "beginning_phase",
    "first_main_phase",
    "combat_phase",
    "second_main_phase",
    "ending_phase",
}


class LobbyError(Exception):
    """HTTP-safe lobby error with status and machine-readable code."""

    status_code: int
    code: str

    def __init__(self, status_code: int, code: str, message: str) -> None:
        """Initialize an HTTP-safe error.

        Args:
            status_code: HTTP status to return.
            code: Stable machine-readable error code.
            message: Human-readable error explanation.
        """
        super().__init__(message)
        self.status_code = status_code
        self.code = code


@dataclass(frozen=True)
class Seat:
    """A fixed lobby position and its Player Specification."""

    index: int
    specification: PlayerSpecification


class Lobby:
    """Own one locked, in-memory lobby and its optional started Game."""

    def __init__(self, expected_players: int = 2, rng: random.Random | None = None) -> None:
        """Initialize an empty Lobby.

        Args:
            expected_players: Required seat count; currently only two is supported.
            rng: Optional random source passed into game setup.

        Raises:
            ValueError: If the requested seat count is not two.
        """
        if expected_players != 2:
            raise ValueError("The server currently supports only two players")
        self.expected_players = expected_players
        self.rng = rng
        self.lock = asyncio.Lock()
        self.event_condition = asyncio.Condition(self.lock)
        self.seats: list[Seat] = []
        self.tokens: dict[str, int] = {}
        self.game: Game | None = None
        self.events: list[EventResponse] = []

    async def join(self, specification: PlayerSpecification) -> JoinResponse:
        """Validate and claim a Seat, starting the Game after the final join.

        Args:
            specification: Player Specification to validate and assign.

        Returns:
            Bearer token and assigned Seat number.

        Raises:
            LobbyError: If the specification is invalid, duplicated, or the lobby is full.
        """
        async with self.lock:
            if len(self.seats) >= self.expected_players:
                raise LobbyError(409, "game_full", "The game already has all expected players")
            validated = self._validate_specification(specification)
            if self._name_is_taken(validated.name):
                raise LobbyError(409, "name_taken", "That player name is already in use")
            pending = [seat.specification for seat in self.seats] + [validated]
            game = (
                self._build_started_game(pending) if len(pending) == self.expected_players else None
            )
            seat = Seat(len(self.seats), validated)
            token = secrets.token_urlsafe(32)
            self.seats.append(seat)
            self.tokens[token] = seat.index
            if game is not None:
                self.game = game
            return JoinResponse(seat=seat.index, token=token)

    def _validate_specification(self, specification: PlayerSpecification) -> PlayerSpecification:
        name = specification.name.strip()
        if not name:
            raise LobbyError(422, "invalid_player_specification", "Player names must not be empty")
        try:
            entries = parse_decklist(specification.decklist)
            decklist_validator.validate(entries, name)
        except ValueError as error:
            raise LobbyError(422, "invalid_player_specification", str(error)) from error
        return PlayerSpecification(name, specification.decklist, specification.starting_life)

    def _name_is_taken(self, name: str) -> bool:
        return any(seat.specification.name.casefold() == name.casefold() for seat in self.seats)

    def _build_started_game(self, specifications: list[PlayerSpecification]) -> Game:
        game = Game.from_player_specification(
            *specifications,
            rng=self.rng,
            auto_play_land=False,
            auto_discard=False,
        )
        self.game = game
        self._append_event("game_started", {"player_count": len(specifications)})
        try:
            game.start_game()
        except Exception:
            self.game = None
            raise
        self._record_game_events(game, 0)
        self._append_event(
            "hands_dealt",
            {"hand_counts": [len(player.hand.get_cards()) for player in game.players]},
        )
        return game

    def _record_game_events(self, game: Game, first_entry: int) -> None:
        for entry in game.event_log[first_entry:]:
            event_type = str(entry["type"])
            data = self._event_data(game, event_type, entry)
            if data is not None:
                self._append_event(event_type, data)

    @staticmethod
    def _event_data(
        game: Game, event_type: str, entry: dict[str, object]
    ) -> dict[str, object] | None:
        if event_type == "game_over":
            result = entry.get("result")
            return Lobby._game_result_data(game, result) if isinstance(result, GameResult) else None
        if event_type == "starting_player":
            player = entry.get("player")
            return {"seat": game.players.index(player)} if isinstance(player, Player) else None
        if "turn" in entry:
            turn = entry["turn"]
            if isinstance(turn, Turn):
                return {
                    "seat": game.players.index(turn.active_player),
                    "turn_number": turn.turn_number,
                }
            return None
        player = entry.get("player")
        if not isinstance(player, Player):
            return None
        data: dict[str, object] = {"seat": game.players.index(player)}
        card = entry.get("card")
        if isinstance(card, Card):
            data["card"] = card.name
        if "cards_remaining" in entry:
            data["cards_remaining"] = entry["cards_remaining"]
        return data

    def _append_event(self, event_type: str, data: dict[str, object]) -> None:
        self.events.append(EventResponse(seq=len(self.events) + 1, type=event_type, data=data))
        self.event_condition.notify_all()

    async def command(
        self, seat_index: int, command_type: str, card_name: str | None
    ) -> EventsResponse:
        """Validate and execute one command under the lobby's state lock.

        Args:
            seat_index: Seat identified by the bearer token.
            command_type: One of play, move, pass, or discard.
            card_name: Required card name for play and discard commands.

        Returns:
            Sequenced events caused by the command, redacted for this Seat.

        Raises:
            LobbyError: If the Seat cannot act or the command is not legal.
        """
        async with self.lock:
            game = self._require_started_game()
            if game.result is not None:
                raise LobbyError(409, "game_over", "The game is over")
            player = self._player_for_seat(game, seat_index)
            if player is not game.turn.active_player:
                raise LobbyError(409, "not_your_turn", "Only the Active Player may issue commands")
            if command_type not in {"play", "move", "pass", "discard"}:
                raise LobbyError(422, "invalid_command", f"Unknown command type: {command_type}")
            if command_type in {"play", "discard"} and not card_name:
                raise LobbyError(422, "missing_card", "This command requires a card name")
            first_new_sequence = len(self.events) + 1
            first_engine_entry = len(game.event_log)
            try:
                self._execute_command(game, player, command_type, card_name)
            except GameActionError as error:
                status_code = 409 if error.code in {"game_over", "not_your_turn"} else 422
                raise LobbyError(status_code, error.code, str(error)) from error
            self._record_game_events(game, first_engine_entry)
            return EventsResponse(events=self._events_for_seat(seat_index, first_new_sequence - 1))

    @staticmethod
    def _execute_command(
        game: Game, player: Player, command_type: str, card_name: str | None
    ) -> None:
        if command_type == "play":
            assert card_name is not None
            game.play_land(player, card_name)
        elif command_type == "move":
            game.move()
        elif command_type == "pass":
            game.pass_turn()
        else:
            assert card_name is not None
            game.discard(player, card_name)

    async def events_after(self, seat_index: int, after: int, wait: float) -> EventsResponse:
        """Long-poll for events after a sequence, redacting private draw data.

        Args:
            seat_index: Seat identified by the bearer token.
            after: Last sequence already received by the client.
            wait: Maximum number of seconds to wait for a new event.

        Returns:
            All currently available later events, with private card data redacted.
        """
        async with self.event_condition:
            deadline = asyncio.get_running_loop().time() + wait
            while not any(event.seq > after for event in self.events):
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    break
                try:
                    await asyncio.wait_for(self.event_condition.wait(), remaining)
                except TimeoutError:
                    break
            return EventsResponse(events=self._events_for_seat(seat_index, after))

    def _events_for_seat(self, seat_index: int, after: int) -> list[EventResponse]:
        return [self._redact_event(seat_index, event) for event in self.events if event.seq > after]

    @staticmethod
    def _redact_event(seat_index: int, event: EventResponse) -> EventResponse:
        data = event.data.copy()
        if event.type == "draw" and data.get("seat") != seat_index:
            data.pop("card", None)
        return EventResponse(seq=event.seq, type=event.type, data=data)

    async def authenticate(self, token: str | None) -> int:
        """Resolve a bearer token to its Seat while holding the state lock.

        Args:
            token: Presented bearer token, if any.

        Returns:
            Zero-based Seat index.

        Raises:
            LobbyError: If the token is absent or invalid.
        """
        async with self.lock:
            if token is None or token not in self.tokens:
                raise LobbyError(401, "unauthorized", "A valid bearer token is required")
            return self.tokens[token]

    async def seat_snapshot(self, seat_index: int) -> SeatResponse:
        """Return the persistent Seat associated with a valid bearer token.

        Args:
            seat_index: Seat index resolved from the bearer token.

        Returns:
            The Seat and its player name.
        """
        async with self.lock:
            if seat_index < 0 or seat_index >= len(self.seats):
                raise LobbyError(404, "seat_not_found", "The requested Seat does not exist")
            seat = self.seats[seat_index]
            return SeatResponse(seat=seat.index, name=seat.specification.name)

    async def game_snapshot(self) -> GameResponse:
        """Build a detached public game-state response under the state lock.

        Returns:
            A response model containing only public game state.
        """
        async with self.lock:
            game = self._require_started_game()
            phase, step = self._phase_and_step(game.current_turn_event)
            return GameResponse(
                active_seat=game.players.index(game.turn.active_player),
                turn_number=game.turn.turn_number,
                phase=phase,
                step=step,
                players=self._player_responses(game),
                battlefield=self._card_responses(game.battlefield.get_cards()),
                result=self._result_response(game),
            )

    @classmethod
    def _player_responses(cls, game: Game) -> list[PlayerResponse]:
        return [
            PlayerResponse(
                seat=index,
                name=player.name,
                life_total=player.life_total,
                hand_count=len(player.hand.get_cards()),
                graveyard=cls._card_responses(player.graveyard.get_cards()),
            )
            for index, player in enumerate(game.players)
        ]

    @staticmethod
    def _result_response(game: Game) -> GameResultResponse | None:
        if game.result is None:
            return None
        return GameResultResponse(**Lobby._game_result_data(game, game.result))

    async def hand_snapshot(
        self, seat_index: int, requested_seat: int | None = None
    ) -> HandResponse:
        """Return the authenticated Seat's hand, rejecting cross-seat requests.

        Args:
            seat_index: Seat identified by the bearer token.
            requested_seat: Optional Seat requested by the caller.

        Returns:
            A response containing only the authenticated Seat's cards.
        """
        async with self.lock:
            if requested_seat is not None and requested_seat != seat_index:
                raise LobbyError(403, "forbidden_seat", "A Seat may only view its own hand")
            game = self._require_started_game()
            player = self._player_for_seat(game, seat_index)
            return HandResponse(
                seat=seat_index,
                cards=self._card_responses(player.hand.get_cards()),
            )

    async def zone_snapshot(
        self,
        zone_name: str,
        seat_index: int,
        requested_seat: int | None = None,
    ) -> ZoneResponse:
        """Return a detached projection of a public Zone or the caller's private Zone.

        Args:
            zone_name: Name of the Zone to read.
            seat_index: Seat identified by the bearer token.
            requested_seat: Optional Seat selector for zone access.

        Returns:
            A detached list of visible cards in the requested Zone.
        """
        async with self.lock:
            game = self._require_started_game()
            zone = zone_name.casefold()
            cards = self._zone_cards(game, zone, seat_index, requested_seat)
            return ZoneResponse(zone=zone, cards=self._card_responses(cards))

    def _zone_cards(
        self, game: Game, zone: str, own_seat: int, requested_seat: int | None
    ) -> list[Card]:
        if zone not in _ZONE_NAMES:
            raise LobbyError(404, "zone_not_found", f"Unknown zone: {zone}")
        if zone in {"hand", "deck"}:
            return self._private_zone_cards(game, zone, own_seat, requested_seat)
        return self._public_zone_cards(game, zone, requested_seat)

    def _private_zone_cards(
        self, game: Game, zone: str, own_seat: int, requested_seat: int | None
    ) -> list[Card]:
        target_seat = own_seat if requested_seat is None else requested_seat
        if target_seat != own_seat:
            raise LobbyError(403, "forbidden_seat", "A Seat may only view its own private zones")
        player = self._player_for_seat(game, target_seat)
        return player.hand.get_cards() if zone == "hand" else player.deck.get_cards()

    def _public_zone_cards(self, game: Game, zone: str, requested_seat: int | None) -> list[Card]:
        if zone == "battlefield":
            return game.battlefield.get_cards()
        if zone == "stack":
            return game.stack.get_cards()
        players = (
            [self._player_for_seat(game, requested_seat)]
            if requested_seat is not None
            else game.players
        )
        return [
            card
            for player in players
            for card in (player.graveyard if zone == "graveyard" else player.exile).get_cards()
        ]

    def _require_started_game(self) -> Game:
        if self.game is None:
            raise LobbyError(409, "game_not_started", "The game has not started")
        return self.game

    @staticmethod
    def _player_for_seat(game: Game, seat_index: int) -> Player:
        if seat_index < 0 or seat_index >= len(game.players):
            raise LobbyError(404, "seat_not_found", "The requested Seat does not exist")
        return game.players[seat_index]

    @staticmethod
    def _card_response(card: Card) -> CardResponse:
        return CardResponse(
            name=card.name,
            card_type=card.card_type,
            tapped=card.tapped,
            owner_seat=card.owner_index,
            controller_seat=card.controller_index,
        )

    @classmethod
    def _card_responses(cls, cards: list[Card]) -> list[CardResponse]:
        return [cls._card_response(card) for card in cards]

    @staticmethod
    def _game_result_data(game: Game, result: GameResult) -> dict[str, object]:
        return {
            "winner_seat": game.players.index(result.winner),
            "loser_seat": game.players.index(result.loser),
            "turn_number": result.turn_number,
            "reason": result.reason,
        }

    @staticmethod
    def _phase_and_step(event: TurnEvent | None) -> tuple[str | None, str | None]:
        if event is None:
            return None, None
        event_name = type(event).log_name
        phase = _PHASE_BY_EVENT_NAME[event_name]
        step = None if event_name in _PHASE_EVENT_NAMES else event_name
        return phase, step
