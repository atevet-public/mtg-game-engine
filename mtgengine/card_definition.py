"""Immutable data container for a Magic: The Gathering card oracle definition."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CardDefinition:
    oracle_id: str
    name: str
    mana_cost: str | None
    type_line: str
    oracle_text: str | None
    colors: tuple[str, ...]
    color_identity: tuple[str, ...]
    keywords: tuple[str, ...]
    power: str | None
    toughness: str | None
    loyalty: int | None
    layout: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "colors", tuple(self.colors))
        object.__setattr__(self, "color_identity", tuple(self.color_identity))
        object.__setattr__(self, "keywords", tuple(self.keywords))
