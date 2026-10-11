"""Tests for the pure interactive command parser."""

import pytest

from mtgengine.client.commands import CommandParseError, parse_command


def test_parser_keeps_card_names_with_spaces_and_accepts_quotes() -> None:
    assert parse_command("play Lightning Bolt").argument == "Lightning Bolt"
    assert parse_command('discard "Island x2"').argument == "Island x2"
    assert parse_command('join "player spec.json"').argument == "player spec.json"


@pytest.mark.parametrize(
    "text",
    ["", "wat", "move now", "list", "play", "join", "help extra", "'broken"],
)
def test_parser_rejects_unknown_or_malformed_commands(text: str) -> None:
    with pytest.raises(CommandParseError):
        parse_command(text)


def test_parser_supports_list_alias_and_plain_commands() -> None:
    assert parse_command("list game_state").action == "list"
    assert parse_command("list battlefield").argument == "battlefield"
    assert parse_command("PASS").action == "pass"
    assert parse_command("quit").action == "quit"
