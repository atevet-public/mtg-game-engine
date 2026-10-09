"""Game class representing a Magic: The Gathering game."""

from __future__ import annotations

import random

from mtgengine import decklist_validator
from mtgengine.card import Card
from mtgengine.decklist import DecklistEntry, parse_decklist
from mtgengine.event_bus import EventBus
from mtgengine.event_logger import EventLogger
from mtgengine.events import (
    CardDiscardedEvent,
    EmptyDeckDrawAttemptedEvent,
    GameOverEvent,
    LandPlayedEvent,
    StartingPlayerSelectedEvent,
)
from mtgengine.game_result import GameResult
from mtgengine.player import Player
from mtgengine.player_specification import PlayerSpecification
from mtgengine.turn import (
    Turn,
    TurnCleanupStepEvent,
    TurnCombatPhaseEvent,
    TurnDrawStepEvent,
    TurnPostcombatMainPhaseEvent,
    TurnPrecombatMainPhaseEvent,
    TurnUntapStepEvent,
    TurnUpkeepStepEvent,
)
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.stack import Stack


class Game:
    """Represents a Magic: The Gathering game."""

    def __init__(self, players: list[Player]) -> None:
        """Initialize a Game with one or more players and shared game zones.

        The battlefield is modeled as a shared zone. Deck, hand, graveyard, and
        exile remain player-owned zones in the current model. The stack is shared.

        Args:
            players: List of players in the game (must have at least one).

        Raises:
            ValueError: If players list is empty.
        """
        if not players:
            raise ValueError("A game must have at least one player")
        self.players: list[Player] = players
        self.events = EventBus()
        self.event_logger = EventLogger(self.events)
        for player in self.players:
            player.events = self.events
        self.battlefield: Battlefield = Battlefield()
        self.stack: Stack = Stack()
        self.turn = Turn(1, self.players[0], self.events)
        self._rng = random.Random()
        self._starting_player: Player | None = None
        self._starting_player_index = 0
        self._starting_player_first_draw_skipped = False
        self._land_drop_used = False
        self._has_started = False
        self.events.subscribe(TurnUntapStepEvent, self._handle_untap_step)
        self.events.subscribe(TurnDrawStepEvent, self._handle_draw_step)
        self.events.subscribe(TurnPrecombatMainPhaseEvent, self._handle_first_main_phase)
        self.events.subscribe(TurnCleanupStepEvent, self._handle_cleanup_step)
        self.events.subscribe(EmptyDeckDrawAttemptedEvent, self._handle_empty_deck_draw_attempt)

        self.result: GameResult | None = None

    @property
    def event_log(self) -> list[dict[str, object]]:
        """Return the event log collected by this game's logger."""
        return self.event_logger.entries

    @classmethod
    def from_player_specification(
        cls,
        *specs: PlayerSpecification,
        rng: random.Random | None = None,
    ) -> Game:
        """Build a two-player game from names and basic-land decklists.

        Args:
            *specs: Exactly two player specifications.
            rng: Random source used for game setup and play. Defaults to a new
                ``random.Random``.

        Returns:
            A game with one constructed Deck for each supplied player.

        Raises:
            ValueError: If the player specifications or decklists are invalid.
        """
        names = cls._validate_player_specifications(specs)
        players = [
            cls._build_player(spec, name, index)
            for index, (spec, name) in enumerate(zip(specs, names))
        ]
        game = cls(players)
        if rng is not None:
            game._rng = rng
        return game

    @staticmethod
    def _validate_player_specifications(specs: tuple[PlayerSpecification, ...]) -> list[str]:
        if len(specs) != 2:
            raise ValueError("A game requires exactly two player specifications")
        names = [spec.name.strip() for spec in specs]
        if any(not name for name in names):
            raise ValueError("Player names must not be empty")
        if len({name.casefold() for name in names}) != len(names):
            raise ValueError("Player names must be unique")
        return names

    @staticmethod
    def _build_player(spec: PlayerSpecification, name: str, owner_index: int) -> Player:
        entries = parse_decklist(spec.decklist)
        decklist_validator.validate(entries, name)
        player = Player(name, life_total=20)
        for entry in entries:
            Game._add_entry_cards(player, entry, owner_index)
        return player

    @staticmethod
    def _add_entry_cards(player: Player, entry: DecklistEntry, owner_index: int) -> None:
        land = Card(
            entry.name,
            "Land",
            owner_index,
            supertypes=["Basic"],
            subtypes=[entry.name],
        )
        player.deck.add_cards(land, entry.quantity)

    def start_game(self) -> None:
        """Start the game: shuffle decks, deal 7 cards to each player, and select first player."""
        self._has_started = True
        self._shuffle_decks()
        self._select_starting_player()
        self._deal_opening_hands()

    def _shuffle_decks(self) -> None:
        for player in self.players:
            player.deck.shuffle(self._rng)

    def _select_starting_player(self) -> None:
        self._starting_player = self._rng.choice(self.players)
        self._starting_player_index = self.players.index(self._starting_player)
        self._starting_player_first_draw_skipped = False
        self.turn = Turn(1, self._starting_player, self.events)
        self.events.emit(StartingPlayerSelectedEvent(self._starting_player))

    def _deal_opening_hands(self) -> None:
        for player in self.players:
            player.draw_from_deck(7)
            if self._is_over():
                return

    def perform_beginning_phase(self) -> None:
        """Perform the beginning phase in order."""
        if self._is_over():
            return
        self.perform_untap_step()
        self.perform_upkeep_step()
        self.perform_draw_step()

    def perform_untap_step(self) -> None:
        """Untap permanents controlled by the active player."""
        if not self._is_over():
            self._emit_step_event(TurnUntapStepEvent)

    def _handle_untap_step(self, event: TurnUntapStepEvent) -> None:
        """Untap permanents owned by the active player."""
        active_index = self.players.index(event.turn.active_player)
        for permanent in self.battlefield.get_cards():
            if permanent.owner_index == active_index:
                permanent.untap()

    def perform_upkeep_step(self) -> None:
        """Resolve upkeep effects for the active player."""
        if not self._is_over():
            self._emit_step_event(TurnUpkeepStepEvent)

    def perform_draw_step(self) -> None:
        """Draw a card for the active player."""
        if not self._is_over():
            self._emit_step_event(TurnDrawStepEvent)

    def _handle_draw_step(self, event: TurnDrawStepEvent) -> None:
        """Draw a card for the active player during the draw step."""
        if self._is_over():
            return
        if (
            event.turn.active_player is self._starting_player
            and not self._starting_player_first_draw_skipped
        ):
            self._starting_player_first_draw_skipped = True
            return
        event.turn.active_player.draw_from_deck(1)

    def perform_first_main_phase(self) -> None:
        """Perform the Active Player's precombat main phase."""
        if not self._is_over():
            self._emit_step_event(TurnPrecombatMainPhaseEvent)

    def _handle_first_main_phase(self, event: TurnPrecombatMainPhaseEvent) -> None:
        """Make an automatic MVP Land Drop during the precombat main phase."""
        if not self._is_over():
            self.perform_play_land()

    def perform_play_land(self) -> bool:
        """Move the first land in the Active Player's hand onto the battlefield."""
        if self._is_over() or self._land_drop_used:
            return False

        player = self.turn.active_player
        land = self._first_land_in_hand(player)
        if land is None:
            return False

        self._move_land_to_battlefield(player, land)
        return True

    @staticmethod
    def _first_land_in_hand(player: Player) -> Card | None:
        return next((card for card in player.hand.get_cards() if card.card_type == "Land"), None)

    def _move_land_to_battlefield(self, player: Player, land: Card) -> None:
        player.hand.remove_card(land)
        land.untap()
        self.battlefield.add_card(land)
        self._land_drop_used = True
        self.events.emit(LandPlayedEvent(player, land))

    def perform_combat_phase(self) -> None:
        """Perform the no-op MVP combat phase."""
        if not self._is_over():
            self._emit_step_event(TurnCombatPhaseEvent)

    def perform_second_main_phase(self) -> None:
        """Perform the no-op MVP postcombat main phase."""
        if not self._is_over():
            self._emit_step_event(TurnPostcombatMainPhaseEvent)

    def perform_cleanup_step(self) -> None:
        """Discard cards until the Active Player has no more than seven."""
        if not self._is_over():
            self._emit_step_event(TurnCleanupStepEvent)

    def _handle_cleanup_step(self, event: TurnCleanupStepEvent) -> None:
        """Discard excess cards from the Active Player's hand to their graveyard."""
        if self._is_over():
            return
        player = event.turn.active_player
        while len(player.hand.get_cards()) > 7:
            self._discard_card(player)

    def _discard_card(self, player: Player) -> None:
        card = player.hand.get_cards()[0]
        player.hand.remove_card(card)
        player.graveyard.add_card(card)
        self.events.emit(CardDiscardedEvent(player, card))

    def advance_to_next_player(self) -> None:
        """Advance the Active Player and count a completed player cycle."""
        if self._is_over():
            return
        active_index = self.players.index(self.turn.active_player)
        next_index = (active_index + 1) % len(self.players)
        turn_number = self.turn.turn_number + (next_index == self._starting_player_index)
        self.turn = Turn(turn_number, self.players[next_index], self.events)
        self._land_drop_used = False

    def advance_turn(self) -> None:
        """Perform the current turn and advance to the next player."""
        if self._is_over():
            return
        self.perform_beginning_phase()
        self.perform_first_main_phase()
        self.perform_combat_phase()
        self.perform_second_main_phase()
        self.perform_cleanup_step()
        self.advance_to_next_player()

    def play(self) -> GameResult:
        """Run the lands-only game until an Empty-Library Loss ends it."""
        if len(self.players) != 2:
            raise ValueError("A game requires exactly two players to play")
        if not self._has_started:
            self.start_game()
        while not self._is_over():
            self.advance_turn()

        assert self.result is not None
        return self.result

    def _handle_empty_deck_draw_attempt(self, event: EmptyDeckDrawAttemptedEvent) -> None:
        if self._is_over():
            return
        loser = event.player
        winner = next(player for player in self.players if player is not loser)
        # TODO: Apply this loss at the next state-based-action check (CR 704.5b).
        self.result = GameResult(winner, loser, self.turn.turn_number)
        self.events.emit(GameOverEvent(self.result))

    def _is_over(self) -> bool:
        return self.result is not None

    def _emit_step_event(self, event_type: type) -> None:
        assert self.turn
        self.events.emit(event_type(self.turn))
