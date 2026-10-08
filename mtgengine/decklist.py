"""Parsing for Moxfield-style decklists."""

import re
from dataclasses import dataclass

_DECKLIST_LINE = re.compile(
    r"(?P<quantity>[1-9]\d*)\s+(?P<name>.+?)"
    r"(?:\s+\((?P<set_code>[A-Za-z0-9]{2,6})\)"
    r"(?:\s+(?P<collector_number>[0-9]+))?)?"
)
_FOIL_MARKER = re.compile(r"\s+\*F\*$", re.IGNORECASE)
_HASH_COMMENT = re.compile(r"\s+#")
_MALFORMED_PRINTING_SUFFIX = re.compile(r"\s+\([A-Za-z0-9]{2,6}\)\s+[A-Za-z0-9-]+\s+\S+")
_MISSING_CARD_NAME = re.compile(r"^[1-9]\d*\s+\([A-Za-z0-9]{2,6}\)(?:\s+[A-Za-z0-9-]+)?$")


@dataclass(frozen=True)
class DecklistEntry:
    """A card quantity and its optional printing identifiers."""

    quantity: int
    name: str
    set_code: str | None
    collector_number: str | None


def parse_decklist(text: str) -> list[DecklistEntry]:
    """Parse card entries from decklist text.

    Args:
        text: Decklist lines in quantity, card-name, optional-printing format.

    Returns:
        Parsed entries in their original order.

    Raises:
        ValueError: If any non-blank line does not match the supported format.
    """
    stripped_lines = (line.strip() for line in text.splitlines())
    entries = (_parse_line(line, line_num) for line_num, line in enumerate(stripped_lines, start=1))
    return [entry for entry in entries if entry is not None]


def _parse_line(line: str, line_number: int) -> DecklistEntry | None:
    stripped_line = line.strip()
    if not stripped_line:
        return None
    match = _DECKLIST_LINE.fullmatch(stripped_line)
    if _is_invalid_line(stripped_line, match):
        raise ValueError(f"Unparseable decklist entry on line {line_number}: {stripped_line!r}")
    assert match is not None
    return DecklistEntry(
        quantity=int(match.group("quantity")),
        name=match.group("name").strip(),
        set_code=match.group("set_code"),
        collector_number=match.group("collector_number"),
    )


def _is_invalid_line(line: str, match: re.Match[str] | None) -> bool:
    return (
        match is None
        or bool(_FOIL_MARKER.search(line))
        or bool(_HASH_COMMENT.search(line))
        or bool(_MALFORMED_PRINTING_SUFFIX.search(line))
        or bool(_MISSING_CARD_NAME.fullmatch(line))
    )
