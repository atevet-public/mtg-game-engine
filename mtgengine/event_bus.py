"""Per-game synchronous event subscription and dispatch."""

from collections.abc import Callable
from typing import TypeVar

from pyventus.events import EventLinker

Event = TypeVar("Event")
EventHandler = Callable[[Event], None]


class _SynchronousEmitter:
    def __init__(self) -> None:
        self._subscribers: list[tuple[type[object] | None, Callable[[object], None]]] = []

    def subscribe(self, event_type: type[Event] | None, handler: EventHandler[Event]) -> None:
        self._subscribers.append((event_type, handler))  # type: ignore[arg-type]

    def emit(self, event: object) -> None:
        for event_type, handler in self._subscribers:
            if event_type is None or event_type is type(event):
                handler(event)


class EventBus:
    """Dispatch events synchronously to subscribers registered on this bus."""

    def __init__(self) -> None:
        self._event_linker: type[EventLinker] = type("GameEventLinker", (EventLinker,), {})
        self._emitter = _SynchronousEmitter()

    def subscribe(self, event_type: type[Event], handler: EventHandler[Event]) -> None:
        """Subscribe a handler to one event type."""
        self._event_linker.on(event_type)(handler)
        self._emitter.subscribe(event_type, handler)

    def subscribe_all(self, handler: Callable[[object], None]) -> None:
        """Subscribe a handler to every event emitted by this bus."""
        self._event_linker.on(Ellipsis)(handler)
        self._emitter.subscribe(None, handler)

    def emit(self, event: object) -> None:
        """Synchronously notify subscribers with the emitted event."""
        self._emitter.emit(event)
