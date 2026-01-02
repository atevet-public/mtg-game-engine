"""Tests for Deck class."""

from src.mtgengine.card import Card
from src.mtgengine.zone import Zone
from src.mtgengine.zone.deck import Deck


class TestDeck:
    """Test suite for the Deck class."""

    def test_deck_initialization(self) -> None:
        """Test Deck initialization."""
        deck = Deck()
        assert deck.name == "Deck"
        assert deck.cards == []

    def test_deck_is_zone(self) -> None:
        """Test that Deck is a Zone."""
        deck = Deck()
        assert isinstance(deck, Zone)

    def test_deck_add_card(self) -> None:
        """Test adding a card to the Deck."""
        deck = Deck()
        card = Card("Card 1")
        deck.add_card(card)
        assert len(deck.cards) == 1
        assert deck.cards[0] == card

    def test_deck_maintains_insertion_order(self) -> None:
        """Test that Deck maintains cards in insertion order."""
        deck = Deck()
        card1 = Card("Card 1")
        card2 = Card("Card 2")
        card3 = Card("Card 3")

        deck.add_card(card1)
        deck.add_card(card2)
        deck.add_card(card3)

        assert deck.cards[0] == card1
        assert deck.cards[1] == card2
        assert deck.cards[2] == card3

    def test_deck_remove_card(self) -> None:
        """Test removing a card from the Deck."""
        deck = Deck()
        card = Card("Card")
        deck.add_card(card)
        deck.remove_card(card)
        assert len(deck.cards) == 0

    def test_deck_get_cards(self) -> None:
        """Test getting cards from the Deck."""
        deck = Deck()
        card1 = Card("Card 1")
        card2 = Card("Card 2")

        deck.add_card(card1)
        deck.add_card(card2)

        cards = deck.get_cards()
        assert len(cards) == 2
        assert cards[0] == card1
        assert cards[1] == card2
