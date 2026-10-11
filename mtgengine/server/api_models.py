"""Pydantic request and response models shared by the MTGTable API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class PlayerSpecificationRequest(BaseModel):
    """Player Specification submitted when taking a Seat."""

    model_config = ConfigDict(extra="forbid")

    name: str
    decklist: str
    starting_life: int = 20


class JoinResponse(BaseModel):
    """Bearer credential and Seat assigned by the lobby."""

    seat: int
    token: str
    token_type: str = "bearer"


class SeatResponse(BaseModel):
    """Seat restored from an existing bearer token."""

    seat: int
    name: str


class EventResponse(BaseModel):
    """Sequenced server-side game or lobby event."""

    seq: int
    type: str
    data: dict[str, object]


class EventsResponse(BaseModel):
    """Events returned by a command or long-poll request."""

    events: list[EventResponse]


class CommandRequest(BaseModel):
    """Player command submitted to the server."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["play", "move", "pass", "discard"]
    card: str | None = None


class CardResponse(BaseModel):
    """Public card characteristics exposed by a query."""

    name: str
    card_type: str
    tapped: bool
    owner_seat: int
    controller_seat: int


class PlayerResponse(BaseModel):
    """Public state for one Seat."""

    seat: int
    name: str
    life_total: int
    hand_count: int
    graveyard: list[CardResponse]


class GameResultResponse(BaseModel):
    """Seat-based projection of a completed Game Result."""

    winner_seat: int
    loser_seat: int
    turn_number: int
    reason: str


class GameResponse(BaseModel):
    """Read-only, public projection of the game state."""

    active_seat: int
    turn_number: int
    phase: str | None
    step: str | None
    players: list[PlayerResponse]
    battlefield: list[CardResponse]
    result: GameResultResponse | None


class HandResponse(BaseModel):
    """The authenticated Seat's private hand."""

    seat: int
    cards: list[CardResponse]


class ZoneResponse(BaseModel):
    """Cards visible in one requested Zone."""

    zone: str
    cards: list[CardResponse]
