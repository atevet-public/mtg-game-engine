"""FastAPI application factory and read-only MTGTable routes."""

import random

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mtgengine.player_specification import PlayerSpecification
from mtgengine.server.api_models import (
    CommandRequest,
    EventsResponse,
    GameResponse,
    HandResponse,
    JoinResponse,
    PlayerSpecificationRequest,
    ZoneResponse,
)
from mtgengine.server.lobby import Lobby, LobbyError


def create_app(expected_players: int = 2, rng: random.Random | None = None) -> FastAPI:
    """Create an isolated server application and in-memory Lobby.

    Args:
        expected_players: Number of Seats required before the Game starts.
        rng: Optional random source for deterministic game setup.

    Returns:
        A FastAPI application with an isolated Lobby.
    """
    lobby = Lobby(expected_players, rng)
    app = FastAPI(title="MTGTable", version="0.1.0")
    app.state.lobby = lobby

    @app.exception_handler(LobbyError)
    async def handle_lobby_error(_request: Request, error: LobbyError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": {"code": error.code, "message": str(error)}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        message = "; ".join(item["msg"] for item in error.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": "invalid_request", "message": message}},
        )

    async def seat_from_authorization(authorization: str | None) -> int:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.casefold() != "bearer" or not token:
            raise LobbyError(401, "unauthorized", "A valid bearer token is required")
        return await lobby.authenticate(token)

    @app.post("/join", response_model=JoinResponse)
    async def join(specification: PlayerSpecificationRequest) -> JoinResponse:
        return await lobby.join(
            PlayerSpecification(
                name=specification.name,
                decklist=specification.decklist,
                starting_life=specification.starting_life,
            )
        )

    @app.get("/game", response_model=GameResponse)
    async def game(authorization: str | None = Header(default=None)) -> GameResponse:
        await seat_from_authorization(authorization)
        return await lobby.game_snapshot()

    @app.get("/players/me/hand", response_model=HandResponse)
    async def hand(
        seat: int | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> HandResponse:
        own_seat = await seat_from_authorization(authorization)
        return await lobby.hand_snapshot(own_seat, seat)

    @app.get("/zones/{zone_name}", response_model=ZoneResponse)
    async def zone(
        zone_name: str,
        seat: int | None = Query(default=None),
        authorization: str | None = Header(default=None),
    ) -> ZoneResponse:
        own_seat = await seat_from_authorization(authorization)
        return await lobby.zone_snapshot(zone_name, own_seat, seat)

    @app.post("/commands", response_model=EventsResponse)
    async def command(
        request: CommandRequest,
        authorization: str | None = Header(default=None),
    ) -> EventsResponse:
        seat = await seat_from_authorization(authorization)
        return await lobby.command(seat, request.type, request.card)

    @app.get("/events", response_model=EventsResponse)
    async def events(
        after: int = Query(default=0, ge=0),
        wait: float = Query(default=30.0, ge=0.0, le=30.0),
        authorization: str | None = Header(default=None),
    ) -> EventsResponse:
        seat = await seat_from_authorization(authorization)
        return await lobby.events_after(seat, after, wait)

    return app
