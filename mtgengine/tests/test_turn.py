from unittest.mock import Mock

from mtgengine.event_bus import EventBus
from mtgengine.turn import (
    Turn,
    TurnBeginningOfCombatStepEvent,
    TurnBeginningPhaseEvent,
    TurnCleanupStepEvent,
    TurnCombatDamageStepEvent,
    TurnCombatPhaseEvent,
    TurnDeclareAttackersStepEvent,
    TurnDeclareBlockersStepEvent,
    TurnDrawStepEvent,
    TurnEndingPhaseEvent,
    TurnEndOfCombatStepEvent,
    TurnEndStepEvent,
    TurnPostcombatMainPhaseEvent,
    TurnPrecombatMainPhaseEvent,
    TurnUntapStepEvent,
    TurnUpkeepStepEvent,
)


class TestTurn:
    def test_turn_class_exists(self) -> None:
        """Test that the Turn class can be instantiated."""
        turn = Turn(turn_number=1, active_player=Mock(), events=EventBus())
        assert isinstance(turn, Turn)

    def test_turn_raises_untap_step_event(self) -> None:
        """Test that the Turn class raises the Untap Step event as it iterates thru steps."""
        is_untapped = False

        def _handle_untap(event: TurnUntapStepEvent) -> None:
            nonlocal is_untapped
            is_untapped = True

        events = EventBus()
        events.subscribe(TurnUntapStepEvent, _handle_untap)
        turn = Turn(turn_number=1, active_player=Mock(), events=events)
        steps = turn.phases_and_steps
        next(steps)
        next(steps)  # Advance to Untap Step

        assert is_untapped is True

    def test_turn_all_phases_and_steps(self) -> None:
        """Test that the Turn class advances all phases and steps."""
        events = (
            TurnBeginningPhaseEvent,
            TurnUntapStepEvent,
            TurnUpkeepStepEvent,
            TurnDrawStepEvent,
            TurnPrecombatMainPhaseEvent,
            TurnCombatPhaseEvent,
            TurnBeginningOfCombatStepEvent,
            TurnDeclareAttackersStepEvent,
            TurnDeclareBlockersStepEvent,
            TurnCombatDamageStepEvent,
            TurnEndOfCombatStepEvent,
            TurnPostcombatMainPhaseEvent,
            TurnEndingPhaseEvent,
            TurnEndStepEvent,
            TurnCleanupStepEvent,
        )

        received_events: list[object] = []
        event_bus = EventBus()
        for event_type in events:
            event_bus.subscribe(event_type, received_events.append)

        turn = Turn(turn_number=1, active_player=Mock(), events=event_bus)
        for _ in turn.phases_and_steps:
            pass

        assert [type(event) for event in received_events] == list(events)
