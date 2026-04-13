from dataclasses import dataclass


@dataclass
class CardDefinition:
    oracle_id: str
    name: str
    mana_cost: str | None
    type_line: str
    oracle_text: str | None
    colors: list[str]
    color_identity: list[str]
    keywords: list[str]
    power: str | None
    toughness: str | None
    loyalty: int | None
    layout: str
