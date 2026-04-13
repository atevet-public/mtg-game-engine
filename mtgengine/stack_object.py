"""Stack object representing a spell or ability on the stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mtgengine.card_definition import CardDefinition
    from mtgengine.player import Player


@dataclass
class StackObject:
    """Represents a spell or ability on the stack waiting to resolve."""

    source: CardDefinition
    controller: Player
    targets: list[Any] = field(default_factory=list)
