"""Tests for ability classes."""


from mtgengine.abilities.ability import (
    ActivatedAbility,
    TriggeredAbility,
    StaticAbility,
)
from mtgengine.abilities.cost import TapCost
from mtgengine.abilities.effect import DrawCardsEffect, ContinuousEffect
from mtgengine.turn import TurnUntapStepEvent
from mtgengine.turn import Turn
from mtgengine.player import Player


class DummyContinuousEffect(ContinuousEffect):
    """Dummy continuous effect for testing."""

    def description(self) -> str:
        return "Creatures you control get +1/+1"

    def apply(self, game) -> None:
        pass


class TestActivatedAbility:
    """Test suite for the ActivatedAbility class."""

    def test_activated_ability_construction(self) -> None:
        """Test ActivatedAbility can be constructed."""
        cost = TapCost()
        effect = DrawCardsEffect(1)
        ability = ActivatedAbility(cost, effect)

        assert ability.cost is cost
        assert ability.effect is effect
        assert ability.is_sorcery_speed is False

    def test_activated_ability_sorcery_speed_default(self) -> None:
        """Test sorcery_speed defaults to False."""
        ability = ActivatedAbility(TapCost(), DrawCardsEffect(1))
        assert ability.is_sorcery_speed is False

    def test_activated_ability_sorcery_speed_true(self) -> None:
        """Test sorcery_speed can be set to True."""
        ability = ActivatedAbility(TapCost(), DrawCardsEffect(1), is_sorcery_speed=True)
        assert ability.is_sorcery_speed is True

    def test_activated_ability_description(self) -> None:
        """Test description format is '{cost}: {effect}'."""
        cost = TapCost()
        effect = DrawCardsEffect(1)
        ability = ActivatedAbility(cost, effect)

        assert ability.description() == "{T}: Draw 1 card"


class TestTriggeredAbility:
    """Test suite for the TriggeredAbility class."""

    def test_triggered_ability_construction(self) -> None:
        """Test TriggeredAbility can be constructed."""
        effect = DrawCardsEffect(1)
        ability = TriggeredAbility(TurnUntapStepEvent, None, effect)

        assert ability.trigger_event_type is TurnUntapStepEvent
        assert ability.condition is None
        assert ability.effect is effect

    def test_triggered_ability_matches_correct_event_type(self) -> None:
        """Test matches returns True for correct event type."""
        ability = TriggeredAbility(TurnUntapStepEvent, None, DrawCardsEffect(1))
        player = Player("Test", 20)
        turn = Turn(1, player)
        event = TurnUntapStepEvent(turn)

        assert ability.matches(event) is True

    def test_triggered_ability_matches_wrong_event_type(self) -> None:
        """Test matches returns False for wrong event type."""
        ability = TriggeredAbility(TurnUntapStepEvent, None, DrawCardsEffect(1))

        class DifferentEvent:
            pass

        event = DifferentEvent()

        assert ability.matches(event) is False

    def test_triggered_ability_matches_with_condition_true(self) -> None:
        """Test matches respects condition callable when it returns True."""

        def condition(event):
            return True

        ability = TriggeredAbility(TurnUntapStepEvent, condition, DrawCardsEffect(1))
        player = Player("Test", 20)
        turn = Turn(1, player)
        event = TurnUntapStepEvent(turn)

        assert ability.matches(event) is True

    def test_triggered_ability_matches_with_condition_false(self) -> None:
        """Test matches respects condition callable when it returns False."""

        def condition(event):
            return False

        ability = TriggeredAbility(TurnUntapStepEvent, condition, DrawCardsEffect(1))
        player = Player("Test", 20)
        turn = Turn(1, player)
        event = TurnUntapStepEvent(turn)

        assert ability.matches(event) is False

    def test_triggered_ability_description(self) -> None:
        """Test description includes event type and effect."""
        ability = TriggeredAbility(TurnUntapStepEvent, None, DrawCardsEffect(2))
        description = ability.description()

        assert "TurnUntapStepEvent" in description
        assert "Draw 2 cards" in description


class TestStaticAbility:
    """Test suite for the StaticAbility class."""

    def test_static_ability_construction(self) -> None:
        """Test StaticAbility can be constructed."""
        effect = DummyContinuousEffect()
        ability = StaticAbility(effect)

        assert ability.effect is effect

    def test_static_ability_description_delegates(self) -> None:
        """Test description delegates to effect.description()."""
        effect = DummyContinuousEffect()
        ability = StaticAbility(effect)

        assert ability.description() == "Creatures you control get +1/+1"
