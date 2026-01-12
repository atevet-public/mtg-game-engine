from unittest.mock import Mock
from mtgengine.turn import Turn, TurnUntapStepEvent
from pyventus.events import EventLinker


class TestTurn:
    def test_turn_class_exists(self) -> None:
        """Test that the Turn class can be instantiated."""
        turn = Turn(turn_number=1, active_player=Mock())
        assert isinstance(turn, Turn)

    def test_turn_next_phase(self) -> None:
        """Test that the Turn class has a method to advance phases."""
        is_untapped = False

        @EventLinker.on(TurnUntapStepEvent)
        def _handle_untap(event: TurnUntapStepEvent) -> None:
            nonlocal is_untapped
            is_untapped = True

        turn = Turn(turn_number=1, active_player=Mock())
        next(turn.steps)

        assert is_untapped is True
