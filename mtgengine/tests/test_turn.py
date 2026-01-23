from unittest.mock import Mock
from mtgengine.turn import (
    Turn,
    TurnUntapStepEvent,
    TurnBeginningPhaseEvent,
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
from pyventus.events import EventLinker


class TestTurn:
    def test_turn_class_exists(self) -> None:
        """Test that the Turn class can be instantiated."""
        turn = Turn(turn_number=1, active_player=Mock())
        assert isinstance(turn, Turn)

    def test_turn_raises_untap_step_event(self) -> None:
        """Test that the Turn class raises the Untap Step event as it iterates thru steps."""
        is_untapped = False

        @EventLinker.on(TurnUntapStepEvent)
        def _handle_untap(event: TurnUntapStepEvent) -> None:
            nonlocal is_untapped
            is_untapped = True

        turn = Turn(turn_number=1, active_player=Mock())
        steps = turn.phases_and_steps
        next(steps)
        next(steps)  # Advance to Untap Step

        assert is_untapped is True

    def test_turn_all_phases_and_steps(self) -> None:
        """Test that the Turn class advances all phases and steps."""
        num_events_handled = 0

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

        @EventLinker.on(*events)
        def _handle_event(event) -> None:
            nonlocal num_events_handled
            num_events_handled += 1

        turn = Turn(turn_number=1, active_player=Mock())
        for _ in turn.phases_and_steps:
            pass

        assert num_events_handled == len(events)
