"""Ability framework for Magic: The Gathering card abilities."""

from mtgengine.abilities.ability import (
    Ability,
    ActivatedAbility,
    TriggeredAbility,
    StaticAbility,
)
from mtgengine.abilities.keyword_ability import KeywordAbility
from mtgengine.abilities.cost import (
    Cost,
    ManaCost as AbilityManaCost,
    TapCost,
    SacrificeCost,
    DiscardCost,
    CompoundCost,
)
from mtgengine.abilities.effect import (
    Effect,
    ContinuousEffect,
    DrawCardsEffect,
    DealDamageEffect,
    GainLifeEffect,
    LoseLifeEffect,
    AddManaEffect,
    DestroyEffect,
    ExileEffect,
    CounterSpellEffect,
    CreateTokenEffect,
    PutCounterEffect,
)

__all__ = [
    "Ability",
    "ActivatedAbility",
    "TriggeredAbility",
    "StaticAbility",
    "KeywordAbility",
    "Cost",
    "AbilityManaCost",
    "TapCost",
    "SacrificeCost",
    "DiscardCost",
    "CompoundCost",
    "Effect",
    "ContinuousEffect",
    "DrawCardsEffect",
    "DealDamageEffect",
    "GainLifeEffect",
    "LoseLifeEffect",
    "AddManaEffect",
    "DestroyEffect",
    "ExileEffect",
    "CounterSpellEffect",
    "CreateTokenEffect",
    "PutCounterEffect",
]
