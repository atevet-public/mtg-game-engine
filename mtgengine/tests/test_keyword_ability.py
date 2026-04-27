"""Tests for KeywordAbility enum."""

import pytest

from mtgengine.abilities.keyword_ability import KeywordAbility


class TestKeywordAbility:
    """Test suite for the KeywordAbility enum."""

    @pytest.mark.parametrize("input_name,expected", [
        ("flying", KeywordAbility.FLYING),
        ("FLYING", KeywordAbility.FLYING),
        ("Flying", KeywordAbility.FLYING),
        ("first strike", KeywordAbility.FIRST_STRIKE),
        ("FIRST STRIKE", KeywordAbility.FIRST_STRIKE),
        ("First Strike", KeywordAbility.FIRST_STRIKE),
        ("trample", KeywordAbility.TRAMPLE),
        ("haste", KeywordAbility.HASTE),
        ("vigilance", KeywordAbility.VIGILANCE),
        ("deathtouch", KeywordAbility.DEATHTOUCH),
        ("lifelink", KeywordAbility.LIFELINK),
        ("hexproof", KeywordAbility.HEXPROOF),
        ("  flying  ", KeywordAbility.FLYING),
        ("  first strike  ", KeywordAbility.FIRST_STRIKE),
    ])
    def test_from_string_valid(self, input_name: str, expected: KeywordAbility) -> None:
        """Test from_string parses valid keyword names case-insensitively."""
        assert KeywordAbility.from_string(input_name) == expected

    @pytest.mark.parametrize("invalid_name", [
        "not_a_keyword",
        "foobar",
        "first-strike",
        "double-strike",
    ])
    def test_from_string_invalid_raises(self, invalid_name: str) -> None:
        """Test from_string raises ValueError for unknown or hyphenated keywords."""
        with pytest.raises(ValueError, match="Unknown keyword ability"):
            KeywordAbility.from_string(invalid_name)
