"""Seat management, game lifecycle, event sequencing, and safe state projections."""

import asyncio
import random
import secrets
from dataclasses import dataclass

from mtgengine import decklist_validator
from mtgengine.card import Card
from mtgengine.decklist import parse_decklist
from mtgengine.events import (
    CardDiscardedEvent,
    CardDrawnEvent,
    EmptyDeckDrawAttemptedEvent,
    GameOverEvent,
    LandPlayedEvent,
    StartingPlayerSelectedEvent,
)
from mtgengine.game import Game
from mtgengine.game_result import GameResult
from mtgengine.player import Player
from mtgengine.player_specification import PlayerSpecification
from mtgengine.server.api_models import (
    CardResponse,
    EventResponse,
    GameResponse,
    GameResultResponse,
    HandResponse,
    JoinResponse,
    PlayerResponse,
    ZoneResponse,
)
from mtgengine.turn import (
    TurnBeginningPhaseEvent,
    TurnCombatPhaseEvent,
    TurnEndingPhaseEvent,
    TurnPostcombatMainPhaseEvent,
    TurnPrecombatMainPhaseEvent,
)


class LobbyError(Exception):
    """HTTP-safe lobby error with status and machine-readable code."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
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
        if expected_players != 2:
            raise ValueError("The server currently supports only two players")
        self.expected_players = expected_players
        self.rng = rng
        self.lock = asyncio.Lock()
        self.seats: list[Seat] = []
        self.tokens: dict[str, int] = {}
        self.game: Game | None = None
        self.events: list[EventResponse] = []

    async def join(self, specification: PlayerSpecification) -> JoinResponse:
        """Validate and claim a Seat, starting the Game after the final join."""
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
        game.events.subscribe_all(lambda event: self._record_game_event(game, event))
        self._append_event("game_started", {"player_count": len(specifications)})
        try:
            game.start_game()
        except Exception:
            self.game = None
            raise
        self._append_event(
            "hands_dealt",
            {"hand_counts": [len(player.hand.get_cards()) for player in game.players]},
        )
        return game

    def _record_game_event(self, game: Game, event: object) -> None:
        if isinstance(event, StartingPlayerSelectedEvent):
            self._append_event("starting_player", {"seat": game.players.index(event.player)})
        elif isinstance(event, CardDrawnEvent):
            self._append_event(
                "draw",
                {
                    "seat": game.players.index(event.player),
                    "card": event.card.name,
                    "cards_remaining": event.cards_remaining,
                },
            )
        elif isinstance(event, EmptyDeckDrawAttemptedEvent):
            self._append_event(
                "empty_deck_draw_attempted", {"seat": game.players.index(event.player)}
            )
        elif isinstance(event, LandPlayedEvent):
            self._append_event(
                "land_drop", {"seat": game.players.index(event.player), "card": event.card.name}
            )
        elif isinstance(event, CardDiscardedEvent):
            self._append_event(
                "discard", {"seat": game.players.index(event.player), "card": event.card.name}
            )
        elif isinstance(event, GameOverEvent):
            self._append_event("game_over", self._game_result_data(game, event.result))

    def _append_event(self, event_type: str, data: dict[str, object]) -> None:
        self.events.append(EventResponse(seq=len(self.events) + 1, type=event_type, data=data))

    async def authenticate(self, token: str | None) -> int:
        """Resolve a bearer token to its Seat while holding the state lock."""
        async with self.lock:
            if token is None or token not in self.tokens:
                raise LobbyError(401, "unauthorized", "A valid bearer token is required")
            return self.tokens[token]

    async def game_snapshot(self) -> GameResponse:
        """Build a detached public game-state response under the state lock."""
        async with self.lock:
            game = self._require_started_game()
            current_event = game.current_turn_event
            phase, step = self._phase_and_step(current_event)
            players = [
                PlayerResponse(
                    seat=index,
                    name=player.name,
                    life_total=player.life_total,
                    hand_count=len(player.hand.get_cards()),
                    graveyard=[
                        self._card_response(game, card) for card in player.graveyard.get_cards()
                    ],
                )
                for index, player in enumerate(game.players)
            ]
            result = (
                GameResultResponse(**self._game_result_data(game, game.result))
                if game.result is not None
                else None
            )
            return GameResponse(
                active_seat=game.players.index(game.turn.active_player),
                turn_number=game.turn.turn_number,
                phase=phase,
                step=step,
                players=players,
                battlefield=[
                    self._card_response(game, card) for card in game.battlefield.get_cards()
                ],
                result=result,
            )

    async def hand_snapshot(
        self, seat_index: int, requested_seat: int | None = None
    ) -> HandResponse:
        """Return the authenticated Seat's hand, rejecting cross-seat requests."""
        async with self.lock:
            if requested_seat is not None and requested_seat != seat_index:
                raise LobbyError(403, "forbidden_seat", "A Seat may only view its own hand")
            game = self._require_started_game()
            player = self._player_for_seat(game, seat_index)
            return HandResponse(
                seat=seat_index,
                cards=[self._card_response(game, card) for card in player.hand.get_cards()],
            )

    async def zone_snapshot(
        self,
        zone_name: str,
        seat_index: int,
        requested_seat: int | None = None,
    ) -> ZoneResponse:
        """Return a detached projection of a public Zone or the caller's private Zone."""
        async with self.lock:
            game = self._require_started_game()
            zone = zone_name.casefold()
            if zone not in {"battlefield", "graveyard", "exile", "stack", "hand", "deck"}:
                raise LobbyError(404, "zone_not_found", f"Unknown zone: {zone_name}")
            if zone in {"hand", "deck"}:
                target_seat = seat_index if requested_seat is None else requested_seat
                if target_seat != seat_index:
                    raise LobbyError(
                        403, "forbidden_seat", "A Seat may only view its own private zones"
                    )
                player = self._player_for_seat(game, target_seat)
                cards = player.hand.get_cards() if zone == "hand" else player.deck.get_cards()
            elif zone == "battlefield":
                cards = game.battlefield.get_cards()
            elif zone == "stack":
                cards = game.stack.get_cards()
            else:
                target_players = (
                    [self._player_for_seat(game, requested_seat)]
                    if requested_seat is not None
                    else game.players
                )
                cards = [
                    card
                    for player in target_players
                    for card in (
                        player.graveyard if zone == "graveyard" else player.exile
                    ).get_cards()
                ]
            return ZoneResponse(
                zone=zone, cards=[self._card_response(game, card) for card in cards]
            )

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
    def _card_response(game: Game, card: Card) -> CardResponse:
        return CardResponse(
            name=card.name,
            card_type=card.card_type,
            tapped=card.tapped,
            owner_seat=card.owner_index,
            controller_seat=card.owner_index,
        )

    @staticmethod
    def _game_result_data(game: Game, result: GameResult) -> dict[str, object]:
        return {
            "winner_seat": game.players.index(result.winner),
            "loser_seat": game.players.index(result.loser),
            "turn_number": result.turn_number,
            "reason": result.reason,
        }

    @staticmethod
    def _phase_and_step(event: object | None) -> tuple[str | None, str | None]:
        if event is None:
            return None, None
        if isinstance(event, TurnBeginningPhaseEvent):
            return "beginning", None
        if isinstance(event, TurnCombatPhaseEvent):
            return "combat", None
        if isinstance(event, TurnEndingPhaseEvent):
            return "ending", None
        if isinstance(event, TurnPrecombatMainPhaseEvent):
            return "main", "precombat_main"
        if isinstance(event, TurnPostcombatMainPhaseEvent):
            return "main", "postcombat_main"
        return "turn", getattr(type(event), "log_name", None)
