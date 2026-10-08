"""Tests for constructing games from player specifications."""

import pytest

from mtgengine import Game, GameResult, PlayerSpecification
from mtgengine.tests.game_test_helpers import SelectSecondPlayerRandom


def create_decklist_entry(card_name: str = "Forest", quantity: int = 60) -> str:
    return f"{quantity} {card_name}"


def test_game_factory_builds_two_players_and_their_basic_land_decks() -> None:
    game = Game.from_player_specification(
        PlayerSpecification("Alice", "2 Forest (M21) 280\n58 Island"),
        PlayerSpecification("Bob", create_decklist_entry("Mountain")),
    )

    assert [player.name for player in game.players] == ["Alice", "Bob"]
    assert [player.life_total for player in game.players] == [20, 20]
    assert [len(player.deck.get_cards()) for player in game.players] == [60, 60]

    alice_cards = game.players[0].deck.get_cards()
    for card in alice_cards[0:2]:
        assert card.name == "Forest"
        assert card.card_type == "Land"
        assert card.owner_index == 0
        assert card.supertypes == ["Basic"]
        assert card.subtypes == ["Forest"]
    for card in alice_cards[2:]:
        assert card.name == "Island"
        assert card.card_type == "Land"
        assert card.owner_index == 0
        assert card.supertypes == ["Basic"]
        assert card.subtypes == ["Island"]

    bob_cards = game.players[1].deck.get_cards()
    for card in bob_cards:
        assert card.name == "Mountain"
        assert card.card_type == "Land"
        assert card.owner_index == 1
        assert card.supertypes == ["Basic"]
        assert card.subtypes == ["Mountain"]


@pytest.mark.parametrize(
    "specifications",
    [
        (),
        (PlayerSpecification("Alice", create_decklist_entry()),),
        (
            PlayerSpecification("Alice", create_decklist_entry()),
            PlayerSpecification("Bob", create_decklist_entry()),
            PlayerSpecification("Cara", create_decklist_entry()),
        ),
    ],
)
def test_game_factory_requires_exactly_two_players(
    specifications: tuple[PlayerSpecification, ...],
) -> None:
    with pytest.raises(ValueError, match="exactly two"):
        Game.from_player_specification(*specifications)


@pytest.mark.parametrize("names", [("", "Bob"), ("  ", "Bob"), (" Alice ", "alice")])
def test_game_factory_rejects_empty_or_duplicate_player_names(names: tuple[str, str]) -> None:
    with pytest.raises(ValueError, match="name"):
        Game.from_player_specification(
            PlayerSpecification(names[0], create_decklist_entry()),
            PlayerSpecification(names[1], create_decklist_entry()),
        )


@pytest.mark.parametrize(
    "cards",
    [
        ("59 Forest",),
        ("60 Sol Ring",),
        ("60 Forest", "59 Plains"),
    ],
)
def test_game_factory_rejects_short_or_nonbasic_decks(cards: tuple[str, ...]) -> None:
    second_deck = cards[1] if len(cards) > 1 else create_decklist_entry()

    with pytest.raises(ValueError, match="deck"):
        Game.from_player_specification(
            PlayerSpecification("Alice", cards[0]),
            PlayerSpecification("Bob", second_deck),
        )


def test_play_returns_result_when_a_player_attempts_to_draw_from_empty_deck() -> None:
    game = Game.from_player_specification(
        PlayerSpecification("Alice", create_decklist_entry()),
        PlayerSpecification("Bob", create_decklist_entry("Island")),
        rng=SelectSecondPlayerRandom(1),
    )

    result = game.play()

    assert result == GameResult(
        winner_name="Bob",
        loser_name="Alice",
        turn_number=54,
        reason="empty_library",
    )
    assert game.is_game_over is True
    assert game.event_log[-1] == {"type": "game_over", "player_index": 0, "reason": "empty_library"}
