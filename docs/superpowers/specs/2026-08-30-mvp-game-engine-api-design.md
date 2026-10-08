# Design: MVP Game Engine API

**Date:** 2026-08-30

## Problem

The repository has a simple MTG engine skeleton (`Game`, `Player`, zones, turn events), but it does not yet model a playable two-player game built from decklists. The project needs an MVP API for a restricted Magic game that is intentionally simple:

- two players only, each described by a `PlayerSpecification` (unique name and decklist text)
- each player has a deck of at least 60 basic lands, supplied as a Moxfield-style decklist
- the engine shuffles decks, randomly picks the Starting Player, and deals 7 cards to each player
- gameplay follows a fixed lands-only turn flow
- the game ends when the active player attempts to draw from an empty deck
- every draw and notable action is recorded in a structured event log
- exact-state snapshot/save/load is a later milestone (see Non-goals)

This MVP must support a strong extension path without overbuilding a full rules engine.

## Goals

- Define a Python in-process API for a small but real game loop
- Build a playable game from decklist text with one factory call and one `play()` call
- Keep the architecture simple enough to ship as a multi-PR effort
- Separate the MVP rules from future generic rules-engine work

## Non-goals

- Snapshot, JSON save/load, and `from_json` (deferred to a later milestone)
- Detection of infinite loops that prevent a game from ending (future work; the MVP game always ends because each draw shrinks a deck)
- Sideboards, decklist headers, `x` quantities, and non-basic-land cards
- Full Magic rules compliance beyond the lands-only MVP
- Generic stack modeling for spells and abilities
- Poison counters, emblems, or other advanced state
- Networked or HTTP API exposure in this milestone
- Full combat rules, mana payment, or card text evaluation

## Rules basis

The design specifically relies on the Comprehensive Rules for lands:

- CR 116.2a: “Playing a land is a special action… it doesn’t use the stack.”
- CR 305.1: “Playing a land is a special action; it doesn’t use the stack… the player simply puts the land onto the battlefield.”
- CR 400.1: Each player has their own library, hand, and graveyard; other zones (including battlefield) are shared.
- CR 403.1: The battlefield is a shared game area that starts empty.

Because a land is not a spell and does not use the stack, the MVP does not include a `Stack` object or stack state in the game model or snapshot.

## Design approach

Use the existing stateful-game pattern, with `Game` as the orchestrator and focused helper methods that mutate the world in a predictable order.

Active-player and turn-number tracking live on `Turn`, not `Game`: `Game` holds a single `turn: Turn` attribute and replaces it wholesale when advancing to the next player/turn, rather than storing a separate `current_player_index` field. Anywhere an index is needed (battlefield ownership, event-log entries, snapshots), it is derived on demand with `self.players.index(self.turn.active_player)`.

Each turn-phase/step `perform_*` method (untap, upkeep, draw, main phases, combat, cleanup) only emits the matching `Turn*Event` through `self.turn._event_emitter`. The actual rule behavior for that step lives in a paired private handler method (e.g. `_handle_untap_step`), registered once in `Game.__init__` via `EventLinker.on(EventType)(self._handle_x)`. This decouples "the turn clock ticked" from "what happens as a result," and matches the emitter/event pattern already used for `perform_beginning_phase`. `perform_play_land()` is the one exception: it's a direct player action, not a turn-clock tick, so it isn't wired through an event.

This keeps the design close to the current repository structure while still allowing clean component-based PRs.

## API shape

The public API is intentionally small and explicit.

```python
@dataclass(frozen=True)
class PlayerSpecification:
    name: str
    decklist: str

@dataclass(frozen=True)
class GameResult:
    winner_name: str
    loser_name: str
    turn_number: int
    reason: str = "empty_library"

class Game:
    def __init__(self, players: list[Player]) -> None: ...
    @classmethod
    def from_player_specification(cls, *specs: PlayerSpecification, rng: random.Random | None = None) -> "Game": ...
    def play(self) -> GameResult: ...
    def start_game(self) -> None: ...
    def perform_beginning_phase(self) -> None: ...
    def perform_untap_step(self) -> None: ...
    def perform_upkeep_step(self) -> None: ...
    def perform_draw_step(self) -> None: ...
    def draw_card_from_deck(self, player: Player | None = None) -> Card | None: ...
    def check_for_empty_deck_loss(self) -> bool: ...
    def perform_first_main_phase(self) -> None: ...
    def perform_play_land(self) -> bool: ...
    def perform_combat_phase(self) -> None: ...
    def perform_second_main_phase(self) -> None: ...
    def perform_cleanup_step(self) -> None: ...
    def advance_to_next_player(self) -> None: ...
    def advance_turn(self) -> None: ...
```

`snapshot`, `to_json`, and `from_json` are deferred.

`from_player_specification` validates all input and builds the players: it requires exactly two specifications (MVP scope; the variadic signature allows 3-4 players later), unique names after trimming and case-folding, and non-empty names. Validation lives in the factory, not in the dataclass. The factory's `rng` is stored on the game and used by `play()` when it calls `start_game`.

The names deliberately use `perform_*` rather than bare step names so the API reads like an action that mutates game state, not just a property or side-effecting callback.

## Decklist input

Format per line: `[Quantity] [Card Name] <([Set Code]) [Collector Number]>`; set code and collector number are optional.

- `mtgengine/decklist.py` provides a frozen `DecklistEntry(quantity, name, set_code, collector_number)` and `parse_decklist(text) -> list[DecklistEntry]`.
- Blank lines and surrounding whitespace are accepted. Anything else unparseable (headers, comments, `x` quantities, sideboards, foil markers) raises `ValueError` including the line number.
- Deck validation is a separate step: at least 60 cards (CR 100.2a) and only Plains, Island, Swamp, Mountain, Forest. Set code and collector number are parsed but ignored by gameplay.
- The factory builds one `Card` per copy: `Card(name, "Land", owner_index, supertypes=["Basic"], subtypes=[name])`. Mana production is not modeled.

## State model

### Player

For the MVP, `Player` stays minimal:

```python
class Player:
    name: str
    deck: Deck
    hand: Hand
    graveyard: Graveyard
    exile: Exile
```

The following are intentionally not added:

- `poison_counters`
- `has_lost`
- `is_active`

These concerns are out of scope for the MVP, and they do not contribute to the required lands-only gameplay loop.

### Game

```python
class Game:
    players: list[Player]
    battlefield: Battlefield
    turn: Turn
    is_game_over: bool
    winner: Player | None
    event_log: list[dict[str, Any]]
```

`turn.turn_number` and `turn.active_player` replace the previously planned `Game.current_player_index`/`Game.turn_number` fields. `Game` never stores a player index directly; it derives one with `self.players.index(self.turn.active_player)` wherever an index is needed (e.g. battlefield ownership, event-log entries, snapshots).

The current implementation includes a shared `stack: Stack` attribute, but the lands-only MVP does not use it yet.
### Battlefield representation

The battlefield is a single shared zone holding `Card` objects, each carrying `owner_index` and `tapped`. No separate land record type exists.

### Game snapshot format (deferred)

Snapshot and JSON save/load are a later milestone. The intended structure, when built, includes `starting_player_index` in addition to:

- the ordered deck contents for each player
- the ordered hand contents for each player
- graveyard contents for each player
- exile contents for each player
- shared battlefield contents as ordered cards with owner metadata
- turn number (`self.turn.turn_number`)
- current player index (`self.players.index(self.turn.active_player)`, computed at snapshot time, not stored on `Game`)
- `is_game_over`
- winner index if present
- event log

Example shape:

```json
{
  "turn_number": 3,
  "current_player_index": 1,
  "is_game_over": false,
  "winner_index": null,
  "players": [
    {
      "name": "Alice",
      "deck": ["Forest", "Forest"],
      "hand": ["Forest", "Forest"],
      "graveyard": [],
      "exile": []
    },
    {
      "name": "Bob",
      "deck": ["Forest"],
      "hand": ["Forest"],
      "graveyard": [],
      "exile": []
    }
  ],
  "battlefield": [
    {"owner_index": 0, "card_name": "Forest", "tapped": false}
  ],
  "event_log": [
    {"type": "starting_player", "player_index": 0},
    {"type": "draw", "player_index": 0, "card": "Forest"}
  ]
}
```

This is the state representation used for persistence and rehydration.

## Turn flow

The MVP turn flow is intentionally narrow and deterministic:

1. `start_game()`
   - shuffle each deck with the injected `random.Random`
   - randomly choose the Starting Player and make them the active player on turn 1; `players` keeps input order, and later turns go to the next index modulo the player count
   - log a `starting_player` event immediately after selection
   - deal 7 cards to each player through the game's draw logic, logging each as an individual `draw` event

2. `perform_beginning_phase()`
   - call `perform_untap_step()`
   - call `perform_upkeep_step()`
   - call `perform_draw_step()`

3. `perform_untap_step()`
   - emits `TurnUntapStepEvent`; the `_handle_untap_step` handler untaps lands on the shared battlefield controlled by `event.turn.active_player`
   - lands are always untapped in this MVP unless later work adds a tap state rule

4. `perform_upkeep_step()`
   - emits `TurnUpkeepStepEvent`; the `_handle_upkeep_step` handler is a no-op besides logging

5. `perform_draw_step()`
   - emits `TurnDrawStepEvent`; the `_handle_draw_step` handler draws one card for the active player, logs a `draw` event, and checks for the empty-deck loss condition
   - the Starting Player skips the draw step of their first turn (CR 103.8a)
   - if the deck is empty, the game ends immediately and the active player loses
   - all actions are logged as structured events

6. `perform_first_main_phase()`
   - emits `TurnPrecombatMainPhaseEvent`; the `_handle_first_main_phase` handler calls `perform_play_land()` if the active player has a land in hand
   - the MVP allows one land drop per turn and nothing else

7. `perform_play_land()`
   - a direct player action (not event-driven, since it's not a turn-clock tick)
   - at most one land drop per turn (CR 116.2a); does nothing if the hand has no land
   - removes the first land in hand and puts it on the shared battlefield
   - always marks it untapped
   - logs a `land_drop` event
   - owner is `self.players.index(self.turn.active_player)`

8. `perform_combat_phase()`
   - emits `TurnCombatPhaseEvent`; the `_handle_combat_phase` handler is a no-op besides logging

9. `perform_second_main_phase()`
   - emits `TurnPostcombatMainPhaseEvent`; the `_handle_second_main_phase` handler is a no-op besides logging

10. `perform_cleanup_step()`
    - emits `TurnCleanupStepEvent`; the `_handle_cleanup_step` handler discards cards above 7 in the active player's hand to the graveyard (CR 514.1), logging a `discard` event for each

11. End-of-turn flow
    - `advance_to_next_player()` replaces `self.turn` with a new `Turn` for the next active player, incrementing `turn_number` once both players have completed a cycle
    - the game continues until an empty-deck draw ends the game

Turn counter semantics:

- `turn.turn_number` starts at 1
- the Starting Player (random index) acts during turn 1
- after the player at index `i` ends their turn, `self.turn` is replaced with the next index modulo the player count, keeping the same `turn_number`
- once the turn returns to the Starting Player, the cycle completes and `turn_number` increments

Event handlers are registered once in `Game.__init__`, e.g. `EventLinker.on(TurnUntapStepEvent)(self._handle_untap_step)`, so they fire regardless of which `Turn` instance emits the event.

This matches the rule that the turn counter increments after each player has completed a turn within the cycle.

## Game over behavior

The MVP game ends when the active player attempts to draw a card from an empty deck during the draw step.

This aligns directly with the rules:

- CR 121.4: A player who attempts to draw from an empty library loses the game the next time a player would receive priority.
- CR 104.3c: If a player is required to draw more cards than remain in their library, they draw what they can and then lose the game the next time a player would receive priority.

For this MVP, the engine will implement a deterministic approximation of that timing by ending the game immediately when the draw attempt fails during `perform_draw_step()`.

The MVP still intentionally excludes unrelated loss/win paths:

- no replacement effect
- no extra draw rules
- no mulligans
- no extra stack interactions

A `game_over` event with `reason: "empty_library"` is logged instead of a `draw` event, and `play()` returns a `GameResult`. The state should read:

```python
Game.is_game_over = True
Game.winner = opponent
```

The losing player is the one who attempted the draw from the empty deck.

## Implementation details

### `draw_card_from_deck()`

This helper is intentionally small and testable.

Responsibilities:

- read the given player's deck (the active player by default; the opening deal passes each player explicitly)
- if the deck is empty, return `None`
- otherwise remove the top card, append it to the hand, and log a `draw` event
- return the card that was drawn

### `check_for_empty_deck_loss()`

This helper is separate from draw logic because the behavior is a distinct game rule and should be testable independently.

Responsibilities:

- inspect the active player’s deck after the draw attempt
- if the deck is empty and the draw failed, set `is_game_over = True`, log a `game_over` event, and record the loss
- update `winner` state

### `perform_play_land()`

Responsibilities:

- check that the active player has a land in hand and has not already made a land drop this turn
- move the first land in hand to the battlefield
- the land keeps `owner_index = self.players.index(self.turn.active_player)`
- mark it as untapped
- log a `land_drop` event

### `perform_first_main_phase()` / `_handle_first_main_phase()`

`perform_first_main_phase()` emits `TurnPrecombatMainPhaseEvent`. The paired `_handle_first_main_phase()` handler is responsible for:

- calling `perform_play_land()` if a land exists in hand and no land has been played this turn
- doing nothing otherwise
- logging the turn-phase state and the action taken

## PR decomposition

The system should be broken into small, reviewable PRs. Each PR should be narrow enough to describe with one responsibility and a clean title.

### Core state PRs

Already in place: zone classes, player zone composition, untap/upkeep/draw steps. Remaining PRs:

1. `Decklist parser`
2. `Deck validation`
3. `PlayerSpecification and Game.from_player_specification`
4. `Starting-player selection`
5. `First-turn draw skip`
6. `Empty-library loss`
7. `Main phase and land drop`
8. `Combat, second main, and cleanup (with discard)`
9. `Turn advance`
10. `Game.play and GameResult`
11. `Event log (starting_player, draw, land_drop, discard, game_over)`

Snapshot and JSON serialization are a later milestone.

This PR set follows the rule that each PR should be roughly a single component or method. It also respects the requested split between draw logic and empty-deck-loss logic, and between land playing and the first-main-phase automation.

## Testing strategy

Testing should be lightweight and rule-driven.

- `test_start_game_deals_seven_cards_to_each_player`
- `test_starting_player_is_chosen_from_injected_rng`
- `test_untap_step_does_not_error_on_empty_battlefield`
- `test_draw_step_draws_one_card`
- `test_draw_step_from_empty_deck_marks_game_over`
- `test_first_main_phase_plays_a_land_if_available`
- `test_play_land_moves_top_land_from_hand_to_battlefield`
- `test_land_is_marked_untapped_when_played`
- `test_only_one_land_drop_per_turn`
- `test_turn_number_increments_only_after_both_players_complete_a_cycle`
- `test_parse_decklist_rejects_unparseable_line_with_line_number`
- `test_player_names_must_be_unique_ignoring_case`
- `test_starting_player_skips_first_draw`
- `test_every_draw_is_logged`
- `test_cleanup_discards_down_to_seven`
- `test_play_returns_game_result`

The engine should remain deterministic (given a seeded `random.Random`) and easy to inspect through the event log.

## Risks and extension points

- The lands-only model is intentionally simple, so future rules like tap/untap timing, mana production, or combat will require a more general permanent abstraction.
- The battlefield and event log should remain generic enough to evolve beyond lands, and to support a future snapshot/save/load pipeline.
- The event log should use structured dictionaries rather than ad hoc strings so future rule debugging remains straightforward.

## Decision summary

This design deliberately chooses the smallest workable engine model:

- no stack
- no poison counters
- no player activity flags
- shared battlefield zone (not per-player battlefield)
- consistent `player_index` keys across battlefield owner fields and event-log player references, always derived via `self.players.index(self.turn.active_player)` rather than stored separately
- explicit `perform_*` methods that emit `Turn*Event`s, with rule behavior implemented in paired `_handle_*` event handlers registered in `Game.__init__`
- battlefield lands with owner metadata
- deterministic two-player turn flow
- ordered zone state, with save/load through a snapshot format deferred

This keeps the MVP focused, testable, and naturally suitable for a phased multi-PR build.
