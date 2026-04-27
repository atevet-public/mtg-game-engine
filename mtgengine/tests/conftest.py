"""Shared test helpers for the mtgengine test suite."""

from mtgengine.card_definition import CardDefinition


def make_card_def(name: str = "Test") -> CardDefinition:
    """Create a minimal CardDefinition for use in tests."""
    return CardDefinition(
        oracle_id="test-id",
        name=name,
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
