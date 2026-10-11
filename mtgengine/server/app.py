"""FastAPI application factory and read-only MTGTable routes."""

import random

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse

from mtgengine.player_specification import PlayerSpecification
from mtgengine.server.api_models import (
    GameResponse,
    HandResponse,
    JoinResponse,
    PlayerSpecificationRequest,
    ZoneResponse,
)
from mtgengine.server.lobby import Lobby, LobbyError


def create_app(expected_players: int = 2, rng: random.Random | None = None) -> FastAPI:
    """Create an isolated server application and in-memory Lobby."""
    lobby = Lobby(expected_players, rng)
    app = FastAPI(title="MTGTable", version="0.1.0")
    app.state.lobby = lobby

    @app.exception_handler(LobbyError)
    async def handle_lobby_error(_request: Request, error: LobbyError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": {"code": error.code, "message": str(error)}},
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

    return app
