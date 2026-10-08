"""Tests for parsing Moxfield-style decklists."""

from dataclasses import FrozenInstanceError

import pytest

from mtgengine.decklist import DecklistEntry, parse_decklist


def test_parse_decklist_reads_card_names_and_quantities() -> None:
    entries = parse_decklist("4 Forest\n1 Island")

    assert entries == [
        DecklistEntry(quantity=4, name="Forest", set_code=None, collector_number=None),
        DecklistEntry(quantity=1, name="Island", set_code=None, collector_number=None),
    ]


def test_parse_decklist_reads_optional_set_and_collector_details() -> None:
    entries = parse_decklist("2 Llanowar Elves (M19) 314\n1 Island (M21)")

    assert entries == [
        DecklistEntry(quantity=2, name="Llanowar Elves", set_code="M19", collector_number="314"),
        DecklistEntry(quantity=1, name="Island", set_code="M21", collector_number=None),
    ]


def test_parse_decklist_preserves_slashes_in_card_names() -> None:
    assert parse_decklist("1 Fire // Ice")[0].name == "Fire // Ice"


def test_parse_decklist_preserves_long_parenthetical_card_names() -> None:
    assert parse_decklist("1 B.F.M. (Big Furry Monster)")[0].name == "B.F.M. (Big Furry Monster)"


def test_parse_decklist_ignores_blank_lines_and_surrounding_whitespace() -> None:
    entries = parse_decklist("  2  Forest  \n\n  1 Island \n")

    assert [entry.name for entry in entries] == ["Forest", "Island"]


@pytest.mark.parametrize(
    "line",
    [
        "Deck",
        "// comment",
        "4x Forest",
        "SB: 2 Forest",
        "4 Forest *F*",
        "4 Forest # comment",
        "4 (M19) 314",
        "1 Forest (M19) 123 extra",
    ],
)
def test_parse_decklist_rejects_unparseable_lines_with_line_number(line: str) -> None:
    with pytest.raises(ValueError, match="line 2"):
        parse_decklist(f"\n{line}")


def test_decklist_entry_is_immutable() -> None:
    entry = DecklistEntry(quantity=1, name="Forest", set_code=None, collector_number=None)

    with pytest.raises(FrozenInstanceError):
        entry.quantity = 2  # type: ignore[misc]
