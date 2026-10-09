"""Build a game event log by observing all events on its event bus."""

from dataclasses import fields, is_dataclass
from typing import Any

from mtgengine.event_bus import EventBus


class EventLogger:
    """Append shallow event records in the order events are emitted."""

    def __init__(self, events: EventBus) -> None:
        self.entries: list[dict[str, Any]] = []
        events.subscribe_all(self._record)

    def _record(self, event: object) -> None:
        if not is_dataclass(event):
            return
        event_name = getattr(type(event), "log_name", None)
        if event_name is None:
            return
        values = {field.name: getattr(event, field.name) for field in fields(event)}
        self.entries.append({"type": event_name, **values})
