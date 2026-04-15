"""Tests for KeywordAbility enum."""

import pytest

from mtgengine.abilities.keyword_ability import KeywordAbility


class TestKeywordAbility:
    """Test suite for the KeywordAbility enum."""

    def test_from_string_case_insensitive(self) -> None:
        """Test from_string works with different cases."""
        assert KeywordAbility.from_string("flying") == KeywordAbility.FLYING
        assert KeywordAbility.from_string("FLYING") == KeywordAbility.FLYING
        assert KeywordAbility.from_string("Flying") == KeywordAbility.FLYING

    def test_from_string_with_spaces(self) -> None:
        """Test from_string works with spaces."""
        assert KeywordAbility.from_string("first strike") == KeywordAbility.FIRST_STRIKE
        assert KeywordAbility.from_string("FIRST STRIKE") == KeywordAbility.FIRST_STRIKE
        assert KeywordAbility.from_string("First Strike") == KeywordAbility.FIRST_STRIKE

    def test_from_string_with_hyphens(self) -> None:
        """Test from_string works with hyphens."""
        assert KeywordAbility.from_string("first-strike") == KeywordAbility.FIRST_STRIKE
        assert KeywordAbility.from_string("double-strike") == KeywordAbility.DOUBLE_STRIKE

    def test_from_string_common_keywords(self) -> None:
        """Test from_string works for common keywords."""
        assert KeywordAbility.from_string("trample") == KeywordAbility.TRAMPLE
        assert KeywordAbility.from_string("haste") == KeywordAbility.HASTE
        assert KeywordAbility.from_string("vigilance") == KeywordAbility.VIGILANCE
        assert KeywordAbility.from_string("deathtouch") == KeywordAbility.DEATHTOUCH
        assert KeywordAbility.from_string("lifelink") == KeywordAbility.LIFELINK
        assert KeywordAbility.from_string("hexproof") == KeywordAbility.HEXPROOF

    def test_from_string_unknown_keyword_raises(self) -> None:
        """Test from_string raises ValueError for unknown keywords."""
        with pytest.raises(ValueError, match="Unknown keyword ability"):
            KeywordAbility.from_string("not_a_keyword")

        with pytest.raises(ValueError, match="Unknown keyword ability"):
            KeywordAbility.from_string("foobar")

    def test_from_string_whitespace_handling(self) -> None:
        """Test from_string handles whitespace correctly."""
        assert KeywordAbility.from_string("  flying  ") == KeywordAbility.FLYING
        assert KeywordAbility.from_string("  first strike  ") == KeywordAbility.FIRST_STRIKE
