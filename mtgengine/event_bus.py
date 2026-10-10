"""Per-game synchronous event subscription and dispatch."""

from collections.abc import Callable
from typing import TypeVar

from pyventus.events import EventLinker, EventSubscriber

Event = TypeVar("Event")
EventHandler = Callable[[Event], None]


class _SynchronousEmitter:
    def __init__(self, event_linker: type[EventLinker]) -> None:
        self._event_linker = event_linker
        self._subscribers: list[
            tuple[type[object] | None, Callable[..., None], EventSubscriber]
        ] = []

    def subscribe(
        self,
        event_type: type[Event] | None,
        handler: EventHandler[Event],
        subscription: EventSubscriber,
    ) -> None:
        self._subscribers.append((event_type, handler, subscription))

    def emit(self, event: object) -> None:
        registered = self._event_linker.get_subscribers_from_events(type(event), Ellipsis)
        for event_type, handler, subscription in self._subscribers:
            if subscription in registered and (event_type is None or event_type is type(event)):
                handler(event)


class EventBus:
    """Dispatch events synchronously to subscribers registered on this bus."""

    def __init__(self) -> None:
        self._event_linker: type[EventLinker] = type("GameEventLinker", (EventLinker,), {})
        self._emitter = _SynchronousEmitter(self._event_linker)

    def subscribe(self, event_type: type[Event], handler: EventHandler[Event]) -> None:
        """Subscribe a handler to one event type."""
        subscription = self._event_linker.subscribe(event_type, event_callback=handler)
        self._emitter.subscribe(event_type, handler, subscription)

    def subscribe_all(self, handler: Callable[[object], None]) -> None:
        """Subscribe a handler to every event emitted by this bus."""
        subscription = self._event_linker.subscribe(Ellipsis, event_callback=handler)
        self._emitter.subscribe(None, handler, subscription)

    def emit(self, event: object) -> None:
        """Synchronously notify subscribers with the emitted event."""
        self._emitter.emit(event)
