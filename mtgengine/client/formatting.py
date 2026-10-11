"""Human-readable formatting for MTGTable query and event responses."""

from collections import Counter
from collections.abc import Mapping


def _mapping_items(response: Mapping[str, object], key: str) -> list[Mapping[str, object]]:
    value = response.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def format_hand(response: Mapping[str, object]) -> str:
    """Group hand cards by name and show copy counts.

    Args:
        response: Hand API response.

    Returns:
        One sorted card name/count per line.
    """
    names = [str(card["name"]) for card in _mapping_items(response, "cards") if "name" in card]
    if not names:
        return "Hand is empty."
    counts = Counter(names)
    return "\n".join(
        f"{name} x{count}" if count > 1 else name
        for name, count in sorted(counts.items(), key=lambda item: item[0].casefold())
    )


def format_game_state(response: Mapping[str, object]) -> str:
    """Summarize turn, active Seat, players, and Battlefield.

    Args:
        response: Game API response.

    Returns:
        A multi-line human-readable state summary.
    """
    players = _mapping_items(response, "players")
    battlefield = _mapping_items(response, "battlefield")
    lines = [
        f"Turn {response.get('turn_number')} — Seat {response.get('active_seat')} active",
        f"Phase: {response.get('phase') or 'not started'} / {response.get('step') or '—'}",
    ]
    for player in players:
        lines.append(
            f"Seat {player.get('seat')}: {player.get('name')} — "
            f"{player.get('life_total')} life, {player.get('hand_count')} cards in hand"
        )
    cards = [str(card["name"]) for card in battlefield if "name" in card]
    lines.append(f"Battlefield: {', '.join(cards) if cards else 'empty'}")
    result = response.get("result")
    if isinstance(result, Mapping):
        lines.append(
            f"Game over: Seat {result.get('winner_seat')} won; "
            f"Seat {result.get('loser_seat')} lost ({result.get('reason')})."
        )
    return "\n".join(lines)


def format_zone(response: Mapping[str, object]) -> str:
    """Format a Zone response as one card name per line.

    Args:
        response: Zone API response.

    Returns:
        Card names or an empty-zone message.
    """
    names = [str(card["name"]) for card in _mapping_items(response, "cards") if "name" in card]
    return "\n".join(names) if names else f"{response.get('zone', 'Zone')} is empty."


def format_event(event: Mapping[str, object]) -> str:
    """Format one sequenced event for asynchronous prompt output.

    Args:
        event: API event with type and data fields.

    Returns:
        A short line suitable for the interactive prompt.
    """
    event_type = str(event.get("type", "event"))
    data = event.get("data", {})
    if not isinstance(data, Mapping):
        return f"Event: {event_type}"
    seat = data.get("seat")
    if event_type == "game_started":
        return "Game started."
    if event_type == "starting_player":
        return f"Seat {seat} goes first."
    if event_type == "hands_dealt":
        return "Opening hands dealt."
    if event_type == "draw":
        return (
            f"Seat {seat} drew {data['card']}." if "card" in data else f"Seat {seat} drew a card."
        )
    if event_type == "land_drop":
        return f"Seat {seat} played {data.get('card')}."
    if event_type == "discard":
        return f"Seat {seat} discarded {data.get('card')}."
    if event_type == "game_over":
        return (
            f"Game over: Seat {data.get('winner_seat')} won; "
            f"Seat {data.get('loser_seat')} lost on turn {data.get('turn_number')} "
            f"({data.get('reason')})."
        )
    if seat is not None:
        return f"Seat {seat}: {event_type.replace('_', ' ')}."
    return f"Event: {event_type.replace('_', ' ')}."
