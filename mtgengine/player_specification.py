"""Input specification for creating a player."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerSpecification:
    """Input required to create one player and their deck."""

    name: str
    decklist: str
