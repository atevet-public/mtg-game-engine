"""Tests for StackObject class."""

from mtgengine.card_definition import CardDefinition
from mtgengine.player import Player
from mtgengine.stack_object import StackObject


class TestStackObject:
    """Test suite for the StackObject class."""

    def test_stack_object_initialization(self) -> None:
        """Test StackObject initializes with source and controller."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Lightning Bolt",
            mana_cost="{R}",
            type_line="Instant",
            oracle_text="Deal 3 damage to any target.",
            colors=["R"],
            color_identity=["R"],
            keywords=[],
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        controller = Player("Alice", 20)

        stack_obj = StackObject(source=definition, controller=controller)

        assert stack_obj.source is definition
        assert stack_obj.controller is controller
        assert stack_obj.targets == []

    def test_stack_object_with_targets(self) -> None:
        """Test StackObject initializes with targets."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Shock",
            mana_cost="{R}",
            type_line="Instant",
            oracle_text="Shock deals 2 damage to any target.",
            colors=["R"],
            color_identity=["R"],
            keywords=[],
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        controller = Player("Alice", 20)
        target_player = Player("Bob", 20)

        stack_obj = StackObject(
            source=definition,
            controller=controller,
            targets=[target_player],
        )

        assert stack_obj.source is definition
        assert stack_obj.controller is controller
        assert len(stack_obj.targets) == 1
        assert stack_obj.targets[0] is target_player

    def test_stack_object_multiple_targets(self) -> None:
        """Test StackObject with multiple targets."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Electrolyze",
            mana_cost="{1}{U}{R}",
            type_line="Instant",
            oracle_text="Electrolyze deals 2 damage divided as you choose among one or two targets.",
            colors=["U", "R"],
            color_identity=["U", "R"],
            keywords=[],
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        controller = Player("Alice", 20)
        target1 = Player("Bob", 20)
        target2 = Player("Charlie", 20)

        stack_obj = StackObject(
            source=definition,
            controller=controller,
            targets=[target1, target2],
        )

        assert len(stack_obj.targets) == 2
        assert stack_obj.targets[0] is target1
        assert stack_obj.targets[1] is target2
