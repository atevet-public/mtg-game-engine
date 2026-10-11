"""Pure parser for the interactive MTGTable prompt."""

import shlex
from dataclasses import dataclass


class CommandParseError(ValueError):
    """Raised when prompt input is not a supported command."""


@dataclass(frozen=True)
class ParsedCommand:
    """Command name and its optional argument."""

    action: str
    argument: str | None = None


def parse_command(text: str) -> ParsedCommand:
    """Parse one prompt line without performing I/O.

    Args:
        text: Raw line entered by the player.

    Returns:
        The normalized action and any command argument.

    Raises:
        CommandParseError: If the command is unknown or malformed.
    """
    try:
        parts = shlex.split(text)
    except ValueError as error:
        raise CommandParseError(str(error)) from error
    if not parts:
        raise CommandParseError("Enter a command or type help")
    action = parts[0].casefold()
    if action in {"move", "pass", "rejoin", "help", "quit"} and len(parts) == 1:
        return ParsedCommand(action)
    if action == "list" and len(parts) == 2:
        return ParsedCommand(action, parts[1].casefold())
    if action == "join" and len(parts) == 2:
        return ParsedCommand(action, parts[1])
    if action in {"play", "discard"} and len(parts) > 1:
        return ParsedCommand(action, " ".join(parts[1:]))
    raise CommandParseError("Unknown or malformed command; type help for commands")
