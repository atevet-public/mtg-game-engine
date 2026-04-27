"""Tests for Permanent class."""

import pytest

from mtgengine.card_definition import CardDefinition
from mtgengine.permanent import Permanent
from mtgengine.player import Player


class TestPermanent:
    """Test suite for the Permanent class."""

    def test_permanent_initialization(self) -> None:
        """Test Permanent initializes with definition, owner, and controller."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Lightning Bolt",
            mana_cost="{R}",
            type_line="Instant",
            oracle_text="Deal 3 damage to any target.",
            colors=("R",),
            color_identity=("R",),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        controller = Player("Bob", 20)

        permanent = Permanent(definition, owner, controller)

        assert permanent.definition is definition
        assert permanent.owner is owner
        assert permanent.controller is controller
        assert permanent.is_tapped is False
        assert permanent.is_summoning_sick is True
        assert permanent.counters == {}
        assert permanent.attached_to is None
        assert permanent.attachments == []

    def test_tap_untapped_permanent(self) -> None:
        """Test tapping an untapped permanent."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Grizzly Bears",
            mana_cost="{1}{G}",
            type_line="Creature — Bear",
            oracle_text=None,
            colors=("G",),
            color_identity=("G",),
            keywords=(),
            power="2",
            toughness="2",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.tap()
        assert permanent.is_tapped is True

    def test_tap_already_tapped_raises(self) -> None:
        """Test tapping an already tapped permanent raises ValueError."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Grizzly Bears",
            mana_cost="{1}{G}",
            type_line="Creature — Bear",
            oracle_text=None,
            colors=("G",),
            color_identity=("G",),
            keywords=(),
            power="2",
            toughness="2",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.tap()
        with pytest.raises(ValueError, match="already tapped"):
            permanent.tap()

    def test_untap_permanent(self) -> None:
        """Test untapping a permanent."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Forest",
            mana_cost=None,
            type_line="Basic Land — Forest",
            oracle_text="{T}: Add {G}.",
            colors=(),
            color_identity=("G",),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.tap()
        assert permanent.is_tapped is True

        permanent.untap()
        assert permanent.is_tapped is False

    def test_untap_already_untapped(self) -> None:
        """Test untapping an already untapped permanent (no error)."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Island",
            mana_cost=None,
            type_line="Basic Land — Island",
            oracle_text="{T}: Add {U}.",
            colors=(),
            color_identity=("U",),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.untap()  # Should not raise
        assert permanent.is_tapped is False

    def test_add_counter(self) -> None:
        """Test adding counters to a permanent."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Walking Ballista",
            mana_cost="{X}{X}",
            type_line="Artifact Creature — Construct",
            oracle_text="Walking Ballista enters with X +1/+1 counters on it.",
            colors=(),
            color_identity=(),
            keywords=(),
            power="0",
            toughness="0",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.add_counter("+1/+1", 3)
        assert permanent.get_counter("+1/+1") == 3

        permanent.add_counter("+1/+1", 2)
        assert permanent.get_counter("+1/+1") == 5

    def test_add_counter_default_amount(self) -> None:
        """Test adding counter defaults to 1."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Ajani, Mentor of Heroes",
            mana_cost="{3}{G}{W}",
            type_line="Legendary Planeswalker — Ajani",
            oracle_text="+1: Distribute three +1/+1 counters among one, two, or three target creatures you control.",
            colors=("G", "W"),
            color_identity=("G", "W"),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=4,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.add_counter("loyalty")
        assert permanent.get_counter("loyalty") == 1

    def test_remove_counter(self) -> None:
        """Test removing counters from a permanent."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Spike Feeder",
            mana_cost="{1}{G}{G}",
            type_line="Creature — Spike",
            oracle_text="Spike Feeder enters with two +1/+1 counters on it.",
            colors=("G",),
            color_identity=("G",),
            keywords=(),
            power="0",
            toughness="0",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.add_counter("+1/+1", 5)
        permanent.remove_counter("+1/+1", 2)
        assert permanent.get_counter("+1/+1") == 3

    def test_remove_counter_to_zero(self) -> None:
        """Test removing all counters removes the entry."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Test Creature",
            mana_cost="{2}",
            type_line="Creature",
            oracle_text=None,
            colors=(),
            color_identity=(),
            keywords=(),
            power="1",
            toughness="1",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.add_counter("+1/+1", 3)
        permanent.remove_counter("+1/+1", 3)
        assert permanent.get_counter("+1/+1") == 0
        assert "+1/+1" not in permanent.counters

    def test_remove_counter_below_zero_clamps(self) -> None:
        """Test removing more counters than available clamps to zero."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Test Creature",
            mana_cost="{2}",
            type_line="Creature",
            oracle_text=None,
            colors=(),
            color_identity=(),
            keywords=(),
            power="1",
            toughness="1",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        permanent.add_counter("+1/+1", 2)
        permanent.remove_counter("+1/+1", 5)
        assert permanent.get_counter("+1/+1") == 0

    def test_get_counter_nonexistent(self) -> None:
        """Test getting a counter type that doesn't exist returns 0."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Test Creature",
            mana_cost="{2}",
            type_line="Creature",
            oracle_text=None,
            colors=(),
            color_identity=(),
            keywords=(),
            power="1",
            toughness="1",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        assert permanent.get_counter("loyalty") == 0

    def test_attached_to_field(self) -> None:
        """Test attached_to field can be set."""
        aura_def = CardDefinition(
            oracle_id="aura-id",
            name="Pacifism",
            mana_cost="{1}{W}",
            type_line="Enchantment — Aura",
            oracle_text="Enchanted creature can't attack or block.",
            colors=("W",),
            color_identity=("W",),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        creature_def = CardDefinition(
            oracle_id="creature-id",
            name="Grizzly Bears",
            mana_cost="{1}{G}",
            type_line="Creature — Bear",
            oracle_text=None,
            colors=("G",),
            color_identity=("G",),
            keywords=(),
            power="2",
            toughness="2",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        aura = Permanent(aura_def, owner, owner)
        creature = Permanent(creature_def, owner, owner)

        aura.attached_to = creature
        assert aura.attached_to is creature

    def test_attachments_field(self) -> None:
        """Test attachments field can be appended to."""
        aura_def = CardDefinition(
            oracle_id="aura-id",
            name="Pacifism",
            mana_cost="{1}{W}",
            type_line="Enchantment — Aura",
            oracle_text="Enchanted creature can't attack or block.",
            colors=("W",),
            color_identity=("W",),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        creature_def = CardDefinition(
            oracle_id="creature-id",
            name="Grizzly Bears",
            mana_cost="{1}{G}",
            type_line="Creature — Bear",
            oracle_text=None,
            colors=("G",),
            color_identity=("G",),
            keywords=(),
            power="2",
            toughness="2",
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        aura = Permanent(aura_def, owner, owner)
        creature = Permanent(creature_def, owner, owner)

        creature.attachments.append(aura)
        assert len(creature.attachments) == 1
        assert creature.attachments[0] is aura

    def test_add_counter_invalid_amount_raises(self) -> None:
        """Test add_counter raises ValueError for amount < 1."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Test",
            mana_cost="{0}",
            type_line="Artifact",
            oracle_text=None,
            colors=(),
            color_identity=(),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        with pytest.raises(ValueError, match="amount must be at least 1"):
            permanent.add_counter("+1/+1", 0)

        with pytest.raises(ValueError, match="amount must be at least 1"):
            permanent.add_counter("+1/+1", -1)

    def test_remove_counter_invalid_amount_raises(self) -> None:
        """Test remove_counter raises ValueError for amount < 1."""
        definition = CardDefinition(
            oracle_id="test-id",
            name="Test",
            mana_cost="{0}",
            type_line="Artifact",
            oracle_text=None,
            colors=(),
            color_identity=(),
            keywords=(),
            power=None,
            toughness=None,
            loyalty=None,
            layout="normal",
        )
        owner = Player("Alice", 20)
        permanent = Permanent(definition, owner, owner)

        with pytest.raises(ValueError, match="amount must be at least 1"):
            permanent.remove_counter("+1/+1", 0)

        with pytest.raises(ValueError, match="amount must be at least 1"):
            permanent.remove_counter("+1/+1", -1)
