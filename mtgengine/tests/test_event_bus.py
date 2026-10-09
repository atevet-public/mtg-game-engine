"""Tests for the per-game event bus."""

from dataclasses import dataclass

from mtgengine.event_bus import EventBus


@dataclass(frozen=True)
class ExampleEvent:
    value: str


def test_event_bus_notifies_subscribers_synchronously_in_subscription_order() -> None:
    bus = EventBus()
    received: list[str] = []

    bus.subscribe(ExampleEvent, lambda event: received.append(f"first:{event.value}"))
    bus.subscribe(ExampleEvent, lambda event: received.append(f"second:{event.value}"))

    bus.emit(ExampleEvent("draw"))

    assert received == ["first:draw", "second:draw"]


def test_event_bus_instances_do_not_share_subscriptions() -> None:
    first_bus = EventBus()
    second_bus = EventBus()
    received: list[ExampleEvent] = []
    first_bus.subscribe(ExampleEvent, received.append)

    second_bus.emit(ExampleEvent("other game"))

    assert received == []
