"""Game class representing a Magic: The Gathering game."""

from __future__ import annotations

import random
from collections.abc import Callable, Iterator

from mtgengine import decklist_validator
from mtgengine.action_errors import (
    CardNotInHandError,
    DiscardNotRequiredError,
    GameNotStartedError,
    GameOverError,
    NoLandDropLeftError,
    NotALandError,
    NotYourTurnError,
    PlayerEliminatedError,
    PlayerNotInGameError,
    WrongPhaseError,
)
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
    TurnEvent,
    TurnPostcombatMainPhaseEvent,
    TurnPrecombatMainPhaseEvent,
    TurnUntapStepEvent,
    TurnUpkeepStepEvent,
)
from mtgengine.zone.battlefield import Battlefield
from mtgengine.zone.stack import Stack


class Game:
    """Represents a Magic: The Gathering game."""

    def __init__(
        self,
        players: list[Player],
        *,
        auto_play_land: bool = True,
        auto_discard: bool = True,
    ) -> None:
        """Initialize a Game with at least two players and shared game zones.

        The battlefield is modeled as a shared zone. Deck, hand, graveyard, and
        exile remain player-owned zones in the current model. The stack is shared.

        Args:
            players: List of players in the game (must have at least two).
            auto_play_land: Whether the legacy automatic Land Drop remains enabled.
            auto_discard: Whether the legacy automatic cleanup discard remains enabled.

        Raises:
            ValueError: If fewer than two players are provided.
        """
        if len(players) < 2:
            raise ValueError("A game requires at least two players")
        self.players: list[Player] = players
        self.auto_play_land = auto_play_land
        self.auto_discard = auto_discard
        self.events = EventBus()
        self.event_logger = EventLogger(self.events)
        for player in self.players:
            player.events = self.events
        self.battlefield: Battlefield = Battlefield()
        self.stack: Stack = Stack()
        self.turn = Turn(1, self.players[0], self.events)
        self._turn_events: Iterator[TurnEvent] = self.turn.phases_and_steps
        self._current_turn_event: TurnEvent | None = None
        self._rng = random.Random()
        self._starting_player: Player | None = None
        self._starting_player_index = 0
        self._starting_player_first_draw_skipped = False
        self._skip_next_turn_counter_increment = False
        self._land_drop_used = False
        self._suppress_automatic_actions = False
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
        auto_play_land: bool = True,
        auto_discard: bool = True,
    ) -> Game:
        """Build a game from names and basic-land decklists.

        Args:
            *specs: Player specifications for at least two players.
            rng: Random source used for game setup and play. Defaults to a new
                ``random.Random``.
            auto_play_land: Whether to retain automatic Land Drops.
            auto_discard: Whether to retain automatic cleanup discards.

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
        game = cls(
            players,
            auto_play_land=auto_play_land,
            auto_discard=auto_discard,
        )
        if rng is not None:
            game._rng = rng
        return game

    @staticmethod
    def _validate_player_specifications(specs: tuple[PlayerSpecification, ...]) -> list[str]:
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
        player = Player(name, life_total=spec.starting_life)
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
        self._skip_next_turn_counter_increment = False
        self.turn = Turn(1, self._starting_player, self.events)
        self._reset_turn_cursor()
        self.events.emit(StartingPlayerSelectedEvent(self._starting_player))

    def _reset_turn_cursor(self) -> None:
        self._turn_events = self.turn.phases_and_steps
        self._current_turn_event = None

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
        if not self._is_over() and self.auto_play_land and not self._suppress_automatic_actions:
            self.perform_play_land()

    def move(self) -> TurnEvent:
        """Emit exactly one phase or step event in the current turn sequence.

        Returns:
            The phase or step event that was emitted.
        """
        self._require_started()
        self._require_not_over()
        if self._player_has_lost(self.turn.active_player):
            self.advance_to_next_player()
        try:
            event = next(self._turn_events)
        except StopIteration:
            self.advance_to_next_player()
            event = next(self._turn_events)
        self._current_turn_event = event
        return event

    def pass_turn(self) -> TurnEvent | None:
        """Skip optional actions, stopping for cleanup choices or next player's first main.

        Returns:
            The event where the game pauses, or ``None`` if the game ends while advancing.
        """
        self._require_started()
        self._require_not_over()
        cleanup_event = self._cleanup_decision_event()
        if cleanup_event is not None:
            return cleanup_event
        self._suppress_automatic_actions = True
        try:
            return self._advance_to_player_decision()
        finally:
            self._suppress_automatic_actions = False

    def _cleanup_decision_event(self) -> TurnCleanupStepEvent | None:
        if isinstance(self._current_turn_event, TurnCleanupStepEvent) and self._is_player_decision(
            self._current_turn_event
        ):
            return self._current_turn_event
        return None

    def _advance_to_player_decision(self) -> TurnEvent | None:
        starting_player = self.turn.active_player
        while not self._is_over():
            event = self.move()
            if self.turn.active_player is not starting_player and isinstance(
                event, TurnPrecombatMainPhaseEvent
            ):
                return event
            if self._is_player_decision(event):
                return event
        return None

    def play_land(self, player: Player, card_name: str) -> None:
        """Play the first matching land from the Active Player's hand.

        Args:
            player: The player attempting the Land Drop.
            card_name: Case-insensitive name of the land to play.
        """
        self._require_active_player(player)
        self._require_main_phase()
        self._require_land_drop_available()
        card = self._find_card_in_hand(player, card_name)
        if card.card_type != "Land":
            raise NotALandError(f"{card.name} is not a land")
        self._move_land_to_battlefield(player, card)

    def discard(self, player: Player, card_name: str) -> None:
        """Discard a named card during cleanup when the hand exceeds its limit.

        Args:
            player: The player attempting to discard.
            card_name: Case-insensitive name of the card to discard.
        """
        self._require_active_player(player)
        self._require_cleanup_step()
        self._require_discard_needed(player)
        card = self._find_card_in_hand(player, card_name)
        player.hand.remove_card(card)
        player.graveyard.add_card(card)
        self.events.emit(CardDiscardedEvent(player, card))

    def _require_main_phase(self) -> None:
        if not isinstance(
            self._current_turn_event,
            (TurnPrecombatMainPhaseEvent, TurnPostcombatMainPhaseEvent),
        ):
            raise WrongPhaseError("A land may only be played during a main phase")

    def _require_land_drop_available(self) -> None:
        if self._land_drop_used:
            raise NoLandDropLeftError("The Active Player has already made a Land Drop")

    def _require_cleanup_step(self) -> None:
        if not isinstance(self._current_turn_event, TurnCleanupStepEvent):
            raise WrongPhaseError("A card may only be discarded during the cleanup step")

    def _require_discard_needed(self, player: Player) -> None:
        if not player.exceeds_maximum_hand_size:
            raise DiscardNotRequiredError("The hand does not exceed Maximum Hand Size")

    def _require_active_player(self, player: Player) -> None:
        self._require_started()
        self._require_not_over()
        if player not in self.players:
            raise PlayerNotInGameError("The player is not part of this game")
        if self._player_has_lost(player):
            raise PlayerEliminatedError("An eliminated player cannot take actions")
        if player is not self.turn.active_player:
            raise NotYourTurnError("Only the Active Player may take this action")

    def _require_started(self) -> None:
        if not self._has_started:
            raise GameNotStartedError("The game has not started")

    def _require_not_over(self) -> None:
        if self._is_over():
            raise GameOverError("The game is over")

    @staticmethod
    def _find_card_in_hand(player: Player, card_name: str) -> Card:
        card = next(
            (
                card
                for card in player.hand.get_cards()
                if card.name.casefold() == card_name.casefold()
            ),
            None,
        )
        if card is None:
            raise CardNotInHandError(f"{card_name} is not in the player's hand")
        return card

    def _is_player_decision(self, event: TurnEvent) -> bool:
        return (
            isinstance(event, TurnCleanupStepEvent)
            and self.turn.active_player.exceeds_maximum_hand_size
        )

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
        """Discard cards above the configured Maximum Hand Size."""
        if not self._is_over():
            self._emit_step_event(TurnCleanupStepEvent)

    def _handle_cleanup_step(self, event: TurnCleanupStepEvent) -> None:
        """Discard excess cards from the Active Player's hand to their graveyard."""
        if self._is_over() or not self.auto_discard or self._suppress_automatic_actions:
            return
        player = event.turn.active_player
        while player.exceeds_maximum_hand_size:
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
        next_seat = self._next_non_losing_seat(active_index)
        if next_seat is None:
            return
        next_index, next_player = next_seat
        completes_turn_cycle = next_index == self._starting_player_index
        turn_number = self.turn.turn_number + (
            completes_turn_cycle and not self._skip_next_turn_counter_increment
        )
        if completes_turn_cycle:
            self._skip_next_turn_counter_increment = False
        self.turn = Turn(turn_number, next_player, self.events)
        self._land_drop_used = False
        self._reset_turn_cursor()

    def advance_turn(self) -> None:
        """Perform the current turn and advance to the next player."""
        if self._is_over():
            return
        if self._player_has_lost(self.turn.active_player):
            self.advance_to_next_player()
            return
        self.perform_beginning_phase()
        if self._player_has_lost(self.turn.active_player):
            self.advance_to_next_player()
            return
        self.perform_first_main_phase()
        self.perform_combat_phase()
        self.perform_second_main_phase()
        self.perform_cleanup_step()
        self.advance_to_next_player()

    def play(self) -> GameResult:
        """Run the lands-only game until an Empty-Library Loss ends it."""
        if not self._has_started:
            self.start_game()
        while not self._is_over():
            self.advance_turn()

        assert self.result is not None
        return self.result

    def _handle_empty_deck_draw_attempt(self, event: EmptyDeckDrawAttemptedEvent) -> None:
        if self._is_over() or event.player not in self.players:
            return
        loser = event.player
        if self._player_has_lost(loser):
            return
        losers = self.result.losers + [loser] if self.result is not None else [loser]
        remaining_players = [player for player in self.players if player not in losers]
        winner = remaining_players[0] if len(remaining_players) == 1 else None
        self.result = GameResult(winner, losers, self.turn.turn_number)
        if winner is None:
            if loser is self._starting_player:
                self._set_next_starting_player(loser)
            return
        # TODO: Apply this loss at the next state-based-action check (CR 704.5b).
        self.events.emit(GameOverEvent(self.result))

    def _set_next_starting_player(self, loser: Player) -> None:
        loser_index = self.players.index(loser)
        next_seat = self._next_non_losing_seat(loser_index)
        if next_seat is None:
            return
        self._starting_player_index, self._starting_player = next_seat
        self._skip_next_turn_counter_increment = True

    def _next_non_losing_seat(self, after_index: int) -> tuple[int, Player] | None:
        for offset in range(1, len(self.players) + 1):
            index = (after_index + offset) % len(self.players)
            player = self.players[index]
            if not self._player_has_lost(player):
                return index, player
        return None

    def _player_has_lost(self, player: Player) -> bool:
        return self.result is not None and player in self.result.losers

    def _is_over(self) -> bool:
        return self.result is not None and self.result.winner is not None

    def _emit_step_event(self, event_type: Callable[[Turn], object]) -> None:
        assert self.turn
        self.events.emit(event_type(self.turn))
