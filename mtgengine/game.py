"""Game class representing a Magic: The Gathering game."""

import random

from pyventus.events import EventLinker

from mtgengine.card import Card
from mtgengine.player import Player
from mtgengine.turn import (
    Turn,
    TurnDrawStepEvent,
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
        Each player keeps an intentional ``player.game`` back-reference for
        event handlers that need shared game context.

        Args:
            players: List of players in the game (must have at least one).

        Raises:
            ValueError: If players list is empty.
        """
        if not players:
            raise ValueError("A game must have at least one player")
        self.players: list[Player] = players
        self.battlefield: Battlefield = Battlefield()
        self.stack: Stack = Stack()
        self.turn = Turn(1, self.players[0])
        for player in self.players:
            player.game = self
        EventLinker.on(TurnUntapStepEvent)(self._handle_untap_step)
        EventLinker.on(TurnUpkeepStepEvent)(self._handle_upkeep_step)

        # Game state flags
        self.is_game_over: bool = False
        self.winner: Player | None = None
        # Indexed event log: list of event dicts with sequential indices
        self.event_log: list[dict[str, object]] = []

    def start_game(self, rng: random.Random | None = None) -> None:
        """Start the game: shuffle decks, deal 7 cards to each player, and select first player.

        Args:
            rng: A random.Random instance for RNG operations. If None, a new Random is created.
        """
        rng = rng or random.Random()

        # Shuffle each player's deck
        for player in self.players:
            player.deck.shuffle(rng)

        # Deal 7 cards to each player
        for player in self.players:
            player.draw_from_deck(7)

    def perform_beginning_phase(self) -> None:
        """Perform the beginning phase in order."""
        self.perform_untap_step()
        self.perform_upkeep_step()
        self.perform_draw_step()

    def perform_untap_step(self) -> None:
        """Untap permanents controlled by the active player."""
        self._emit_step_event(TurnUntapStepEvent)

    def _handle_untap_step(self, event: TurnUntapStepEvent) -> None:
        """Untap permanents owned by the active player."""
        active_index = self.players.index(event.turn.active_player)
        for permanent in self.battlefield.get_cards():
            if permanent.owner_index == active_index:
                permanent.untap()

    def perform_upkeep_step(self) -> None:
        """Resolve upkeep effects for the active player."""
        self._emit_step_event(TurnUpkeepStepEvent)

    def _handle_upkeep_step(self, event: TurnUpkeepStepEvent) -> None:
        """Log the active player's upkeep step."""
        self.event_log.append(
            {
                "type": "upkeep_step",
                "player_index": self.players.index(event.turn.active_player),
            }
        )

    def perform_draw_step(self) -> None:
        """Draw a card for the active player."""
        self._emit_step_event(TurnDrawStepEvent)

    def draw_card_from_deck(self) -> Card | None:
        """Draw the active player's top card into their hand."""
        player = self.turn.active_player
        if not player.deck.get_cards():
            return None
        card = player.deck.draw(1)[0]
        player.hand.add_card(card)
        return card

    def _emit_step_event(self, event_type: type) -> None:
        assert self.turn
        self.turn._event_emitter.emit(event_type(self.turn))
