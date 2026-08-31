# Design: MVP Game Engine API

**Date:** 2026-08-30

## Problem

The repository has a simple MTG engine skeleton (`Game`, `Player`, zones, turn events), but it does not yet model a playable two-player game with a minimal, serializable state. The project needs an MVP API for a restricted Magic game that is intentionally simple:

- two players only
- each player has a 60-card deck composed of basic lands only
- deck order matters and must be serializable
- each player starts with 7 cards in hand
- gameplay follows a fixed lands-only turn flow
- the game ends when the active player attempts to draw from an empty deck
- the engine must preserve the exact game state so it can be saved and reloaded at any time

This MVP must support a strong extension path without overbuilding a full rules engine.

## Goals

- Define a Python in-process API for a small but real game loop
- Model the exact state necessary for a game snapshot
- Support save/load by serializing the full game state to JSON-like structures
- Keep the architecture simple enough to ship as a multi-PR effort
- Separate the MVP rules from future generic rules-engine work

## Non-goals

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

This keeps the design close to the current repository structure while still allowing clean component-based PRs.

## API shape

The public API is intentionally small and explicit.

```python
class Game:
    def __init__(self, players: list[Player]) -> None: ...
    def start_game(self) -> None: ...
    def perform_beginning_phase(self) -> None: ...
    def perform_untap_step(self) -> None: ...
    def perform_upkeep_step(self) -> None: ...
    def perform_draw_step(self) -> None: ...
    def draw_card_from_deck(self) -> Card | None: ...
    def check_for_empty_deck_loss(self) -> bool: ...
    def perform_first_main_phase(self) -> None: ...
    def perform_play_land(self) -> bool: ...
    def perform_combat_phase(self) -> None: ...
    def perform_second_main_phase(self) -> None: ...
    def perform_cleanup_step(self) -> None: ...
    def advance_to_next_player(self) -> None: ...
    def advance_turn(self) -> None: ...
    def snapshot(self) -> GameSnapshot: ...
    def to_json(self) -> str: ...
    def from_json(self, payload: str) -> "Game": ...
```

The names deliberately use `perform_*` rather than bare step names so the API reads like an action that mutates game state, not just a property or side-effecting callback.

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
    current_player_index: int
    turn_number: int
    is_game_over: bool
    winner: Player | None
    event_log: list[dict[str, Any]]
```

The game does not store a `stack` attribute because lands are not cast as spells and never use the stack.

### Battlefield representation

For the MVP, the battlefield is a single shared zone and consists only of lands. Each land record carries owner metadata so a snapshot can reconstruct who controls each permanent.

```python
@dataclass(frozen=True)
class BattlefieldLand:
    owner_index: int
    card_name: str
    tapped: bool = False
```

This is enough to serialize battlefield state with no generic permanent model.

### Game snapshot format

The game state should be serialized as a JSON-friendly structure that includes:

- the ordered deck contents for each player
- the ordered hand contents for each player
- graveyard contents for each player
- exile contents for each player
- shared battlefield contents as ordered land records with owner metadata
- turn number
- current player index
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
    {"type": "start_game", "player_indices": [0, 1]},
    {"type": "draw", "player_index": 0, "card": "Forest"}
  ]
}
```

This is the state representation used for persistence and rehydration.

## Turn flow

The MVP turn flow is intentionally narrow and deterministic:

1. `start_game()`
   - validate exactly two players
   - deal 7 cards to each player from the top of their deck
   - set `current_player_index = 0`
   - set `turn_number = 1`
   - record setup log entries

2. `perform_beginning_phase()`
   - call `perform_untap_step()`
   - call `perform_upkeep_step()`
   - call `perform_draw_step()`

3. `perform_untap_step()`
   - untap lands on the shared battlefield controlled by the active player
   - lands are always untapped in this MVP unless later work adds a tap state rule

4. `perform_upkeep_step()`
   - no-op for the lands-only MVP

5. `perform_draw_step()`
   - active player draws one card from the top of their deck
   - if the deck is empty, the game ends immediately and the active player loses
   - all actions are logged as structured events

6. `perform_first_main_phase()`
   - active player may play one land per turn if they have one in hand
   - the MVP does not implement full land-per-turn timing rules beyond the basic “play a land if available” behavior
   - implemented as a helper that moves the top land from hand to battlefield

7. `perform_play_land()`
   - deletes the top land from hand
   - appends a new land record to the shared battlefield
   - always marks it untapped
   - owner is the active player

8. `perform_combat_phase()`
   - no-op for the lands-only MVP

9. `perform_second_main_phase()`
   - no-op for the lands-only MVP

10. `perform_cleanup_step()`
    - no-op for the lands-only MVP

11. End-of-turn flow
    - after both players complete a cycle, `turn_number` increments
    - `current_player_index` changes to the next active player
    - the game continues until an empty-deck draw ends the game

Turn counter semantics:

- `turn_number` starts at 1
- player 0 acts during turn 1
- after player 0 ends turn 1, `current_player_index` becomes 1 and `turn_number` still remains 1
- after player 1 ends turn 1, the cycle completes and `turn_number` becomes 2

This matches the rule that the turn counter increments after each player has completed a turn within the cycle.

## Game over behavior

The MVP game ends when the active player attempts to draw a card from an empty deck during the draw step.

This is not a generic “lose if you run out of cards” rule. It is a specific, deterministic game-ending condition that matches the requested MVP behavior:

- no replacement effect
- no extra draw rules
- no mulligans
- no extra stack interactions
- immediate loss when the draw attempt fails

The state should then read:

```python
Game.is_game_over = True
Game.winner = opponent
```

The losing player is the one who attempted the draw from the empty deck.

## Implementation details

### `draw_card_from_deck()`

This helper is intentionally small and testable.

Responsibilities:

- read the active player’s deck
- if the deck is empty, return `None`
- otherwise remove the top card and append it to the hand
- return the card that was drawn

### `check_for_empty_deck_loss()`

This helper is separate from draw logic because the behavior is a distinct game rule and should be testable independently.

Responsibilities:

- inspect the active player’s deck after the draw attempt
- if the deck is empty and the draw failed, set `is_game_over = True` and record the loss
- update `winner` and `loser` state

### `perform_play_land()`

Responsibilities:

- check that the active player has a land in hand
- move the top land from hand to battlefield
- create a battlefield land record with `owner_index = current_player_index`
- mark it as untapped
- log the action

### `perform_first_main_phase()`

Responsibilities:

- call `perform_play_land()` if a land exists in hand
- do nothing if a land does not exist
- log the turn-phase state and the action taken

## PR decomposition

The system should be broken into small, reviewable PRs. Each PR should be narrow enough to describe with one responsibility and a clean title.

### Core state PRs

1. `Zone base classes and ordered zone behavior`
2. `Player state and zone composition`
3. `Game initialization and start_game`

### Turn and rule PRs

4. `Game.perform_beginning_phase`
5. `Game.perform_untap_step`
6. `Game.perform_upkeep_step`
7. `Game.perform_draw_step`
8. `Game.draw_card_from_deck`
9. `Game.check_for_empty_deck_loss`
10. `Game.perform_first_main_phase`
11. `Game.perform_play_land`
12. `Game.perform_combat_phase`
13. `Game.perform_second_main_phase`
14. `Game.perform_cleanup_step`
15. `Game.advance_to_next_player`
16. `Game.advance_turn`
17. `Game.snapshot and JSON serialization`
18. `Game event log and structured state trace`

This PR set follows the rule that each PR should be roughly a single component or method. It also respects the requested split between draw logic and empty-deck-loss logic, and between land playing and the first-main-phase automation.

## Testing strategy

Testing should be lightweight and rule-driven.

- `test_start_game_deals_seven_cards_to_each_player`
- `test_turn_starts_with_player_zero`
- `test_untap_step_does_not_error_on_empty_battlefield`
- `test_draw_step_draws_one_card`
- `test_draw_step_from_empty_deck_marks_game_over`
- `test_first_main_phase_plays_a_land_if_available`
- `test_play_land_moves_top_land_from_hand_to_battlefield`
- `test_land_is_marked_untapped_when_played`
- `test_turn_number_increments_only_after_both_players_complete_a_cycle`
- `test_snapshot_includes_battlefield_land_owner_information`
- `test_round_trip_snapshot_round_trips_to_JSON`

The engine should remain deterministic and easy to inspect through logs and snapshots.

## Risks and extension points

- The lands-only model is intentionally simple, so future rules like tap/untap timing, mana production, or combat will require a more general permanent abstraction.
- The `battlefield` and `snapshot` code should remain generic enough to evolve beyond lands without rewriting the full save/load pipeline.
- The event log should use structured dictionaries rather than ad hoc strings so future rule debugging remains straightforward.

## Decision summary

This design deliberately chooses the smallest workable engine model:

- no stack
- no poison counters
- no player activity flags
- shared battlefield zone (not per-player battlefield)
- consistent `player_index` keys across battlefield owner fields and event-log player references
- explicit `perform_*` methods
- battlefield lands with owner metadata
- deterministic two-player turn flow
- save/load through a snapshot format built around ordered zone state

This keeps the MVP focused, testable, and naturally suitable for a phased multi-PR build.
