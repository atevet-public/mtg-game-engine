# MVP Game Engine API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-player, lands-only MTG MVP engine API with deterministic turn flow, empty-library loss, shared battlefield, and JSON save/load snapshots.

**Architecture:** Keep `Game` as the orchestrator with explicit `perform_*` methods. Use a shared `Battlefield` zone at the game level, keep per-player private zones (deck/hand/graveyard/exile), and model battlefield lands with `owner_index`. Log actions with `player_index` consistently, and expose full-state snapshot serialization.

**Tech Stack:** Python 3, dataclasses, pytest, existing `mtgengine` package layout, `make test`, `make lint`

---

## Multi-agent / Multi-PR execution strategy

### Branch/worktree model

- Create one worktree per PR under `.worktrees/`.
- Keep one branch per PR, based on `main` unless dependency requires another PR branch.
- Use PR chain only when API dependencies require it.

### Dependency waves

1. **Wave 1 (serial foundation):** PR-01, PR-02, PR-03  
2. **Wave 2 (can parallelize after Wave 1):** PR-04, PR-05, PR-06  
3. **Wave 3 (draw/loss pipeline, partial parallel):** PR-07, PR-08, PR-09  
4. **Wave 4 (main-phase land play split):** PR-10, PR-11  
5. **Wave 5 (independent no-op phase PRs in parallel):** PR-12, PR-13, PR-14  
6. **Wave 6 (turn progression serial):** PR-15, PR-16  
7. **Wave 7 (state persistence serial):** PR-17, PR-18  

---

### Task 1 (PR-01): Move battlefield to shared `Game` zone — DONE (merged)

**Files:**
- Modify: `mtgengine/player.py`
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_player.py`
- Test: `mtgengine/tests/test_game.py`

- [x] **Step 1: Write failing tests**
```python
def test_player_does_not_own_battlefield_zone() -> None:
    player = Player("Alice", 20)
    assert not hasattr(player, "battlefield")

def test_game_has_shared_battlefield_zone() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    assert isinstance(game.battlefield, Battlefield)
```

- [ ] **Step 2: Run tests to verify failure**
Run: `pytest mtgengine/tests/test_player.py::test_player_does_not_own_battlefield_zone mtgengine/tests/test_game.py::test_game_has_shared_battlefield_zone -v`  
Expected: FAIL (missing behavior)

- [ ] **Step 3: Implement minimal code**
```python
# mtgengine/player.py
class Player:
    def __init__(self, name: str, life_total: int) -> None:
        self.name = name
        self.life_total = life_total
        self.deck = Deck()
        self.hand = Hand()
        self.graveyard = Graveyard()
        self.exile = Exile()

# mtgengine/game.py
self.battlefield = Battlefield()
```

- [x] **Step 4: Re-run tests**
Run: same pytest command  
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add mtgengine/player.py mtgengine/game.py mtgengine/tests/test_player.py mtgengine/tests/test_game.py
git commit -m "refactor: make battlefield a shared game zone"
```

### Task 2 (PR-02): Deterministic start-game setup — DONE (merged; active player now tracked via `Turn`, not a stored index)

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [x] **Step 1: Write failing tests**
```python
def test_start_game_sets_player_zero_active() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    # preload 60 lands in each deck
    game.start_game()
    assert game.turn.active_player is game.players[0]
    assert game.turn.turn_number == 1
```

- [x] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_start_game_sets_player_zero_active -v`  
Expected: FAIL

- [x] **Step 3: Implement minimal code**
```python
def start_game(self, rng: random.Random | None = None) -> None:
    rng = rng or random.Random()
    for player in self.players:
        player.deck.shuffle(rng)
    for player in self.players:
        player.draw_from_deck(7)
```
Note: `self.turn = Turn(1, self.players[0])` is set once in `Game.__init__`, not in `start_game()`.

- [x] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add deterministic start_game setup"
```

### Task 3 (PR-03): Add `is_game_over`, winner tracking, and indexed event log — DONE (merged)

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [x] **Step 1: Write failing tests**
```python
def test_game_state_flags_initialize() -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    assert game.is_game_over is False
    assert game.winner is None
    assert game.event_log == []
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_game_state_flags_initialize -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
self.is_game_over = False
self.winner = None
self.event_log: list[dict[str, object]] = []
```

- [x] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: initialize game-over flags and event log"
```

### Task 4 (PR-04): Implement `perform_beginning_phase` — DONE (merged; establishes the emit-only step pattern used by later tasks)

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [x] **Step 1: Write failing test**
```python
def test_perform_beginning_phase_calls_steps_in_order(mocker) -> None:
    game = Game([Player("Alice", 20), Player("Bob", 20)])
    untap = mocker.patch.object(game, "perform_untap_step")
    upkeep = mocker.patch.object(game, "perform_upkeep_step")
    draw = mocker.patch.object(game, "perform_draw_step")
    game.perform_beginning_phase()
    untap.assert_called_once()
    upkeep.assert_called_once()
    draw.assert_called_once()
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_beginning_phase_calls_steps_in_order -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_beginning_phase(self) -> None:
    self.perform_untap_step()
    self.perform_upkeep_step()
    self.perform_draw_step()
```

- [x] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [x] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add perform_beginning_phase orchestration"
```

Actual implementation note: `perform_untap_step`/`perform_upkeep_step`/`perform_draw_step` each just call `self._emit_step_event(EventType)`, which emits `EventType(self.turn)` through `self.turn._event_emitter`. Tasks 5-9 below assume this emit-only shape plus paired `_handle_*` event handlers, rather than inline logic in the `perform_*` methods.

### Task 5 (PR-05): Implement `perform_untap_step` via `_handle_untap_step` event handler

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_untap_step_only_untaps_active_players_lands() -> None:
    game = seeded_game_with_lands_on_battlefield()  # lands belong to game.turn.active_player
    game.perform_untap_step()
    assert all(not land.tapped for land in active_player_lands(game))
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_untap_step_only_untaps_active_players_lands -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
# perform_untap_step already exists as: self._emit_step_event(TurnUntapStepEvent)

def _handle_untap_step(self, event: TurnUntapStepEvent) -> None:
    active_index = self.players.index(event.turn.active_player)
    for permanent in self.battlefield.get_cards():
        if permanent.owner_index == active_index:
            permanent.untap()

# In Game.__init__:
EventLinker.on(TurnUntapStepEvent)(self._handle_untap_step)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add untap-step handler for active player permanents"
```

### Task 6 (PR-06): Implement `_handle_upkeep_step` as no-op with log

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_upkeep_step_logs_event() -> None:
    game = seeded_game()
    game.perform_upkeep_step()
    assert game.event_log[-1]["type"] == "upkeep_step"
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_upkeep_step_logs_event -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
# perform_upkeep_step already exists as: self._emit_step_event(TurnUpkeepStepEvent)

def _handle_upkeep_step(self, event: TurnUpkeepStepEvent) -> None:
    self.event_log.append({
        "type": "upkeep_step",
        "player_index": self.players.index(event.turn.active_player),
    })

# In Game.__init__:
EventLinker.on(TurnUpkeepStepEvent)(self._handle_upkeep_step)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add upkeep-step no-op logging handler"
```

### Task 7 (PR-07): Implement `draw_card_from_deck`

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_draw_card_from_deck_moves_top_card_to_hand() -> None:
    game = seeded_game()
    card = game.draw_card_from_deck()
    assert card is not None
    assert card in game.turn.active_player.hand.get_cards()
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_draw_card_from_deck_moves_top_card_to_hand -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def draw_card_from_deck(self) -> Card | None:
    player = self.turn.active_player
    cards = player.deck.draw(1) if player.deck.get_cards() else []
    if not cards:
        return None
    card = cards[0]
    player.hand.add_card(card)
    return card
```
This helper is a plain method (not event-driven) since it's called directly from `_handle_draw_step`.

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add draw_card_from_deck helper"
```

### Task 8 (PR-08): Implement `check_for_empty_deck_loss`

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_check_for_empty_deck_loss_sets_game_outcome() -> None:
    game = empty_deck_game()  # empty deck belongs to game.turn.active_player
    did_lose = game.check_for_empty_deck_loss()
    assert did_lose is True
    assert game.is_game_over is True
    assert game.winner == game.players[1]
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_check_for_empty_deck_loss_sets_game_outcome -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def check_for_empty_deck_loss(self) -> bool:
    # pseudo-code
    # if the active player's deck is empty and they would draw a card
    #   Record the loss
    #   Update state to reflect the winner
    #   return True
    # else
    #   return False
```
This is a plain method (not event-driven) so it stays independently testable.

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add empty-library loss rule helper"
```

### Task 9 (PR-09): Implement `_handle_draw_step` event handler

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_draw_step_draws_or_ends_game(mocker) -> None:
    game = seeded_game()
    draw = mocker.patch.object(game, "draw_card_from_deck", return_value=None)
    loss = mocker.patch.object(game, "check_for_empty_deck_loss", return_value=True)
    game.perform_draw_step()
    draw.assert_called_once()
    loss.assert_called_once()
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_draw_step_draws_or_ends_game -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
# perform_draw_step already exists as: self._emit_step_event(TurnDrawStepEvent)

def _handle_draw_step(self, event: TurnDrawStepEvent) -> None:
    self.draw_card_from_deck()
    self.event_log.append({
        "type": "draw_step",
        "player_index": self.players.index(event.turn.active_player),
    })
    self.check_for_empty_deck_loss()

# In Game.__init__:
EventLinker.on(TurnDrawStepEvent)(self._handle_draw_step)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add draw-step handler"
```

### Task 10 (PR-10): Implement `perform_play_land`

**Files:**
- Modify: `mtgengine/game.py`
- Modify: `mtgengine/card.py` (if needed for owner metadata carrier)
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_play_land_moves_top_land_to_shared_battlefield() -> None:
    game = seeded_game()
    active_index = game.players.index(game.turn.active_player)
    played = game.perform_play_land()
    assert played is True
    assert game.battlefield.get_cards()[-1].owner_index == active_index
    assert game.battlefield.get_cards()[-1].tapped is False
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_play_land_moves_top_land_to_shared_battlefield -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_play_land(self) -> bool:
    player = self.turn.active_player
    hand_cards = player.hand.get_cards()
    if not hand_cards:
        return False
    land = hand_cards[-1]
    player.hand.remove_card(land)
    land.owner_index = self.players.index(player)
    land.tapped = False
    self.battlefield.add_card(land)
    self.event_log.append({
        "type": "play_land",
        "player_index": self.players.index(player),
    })
    return True
```
This is a direct player-action method, not routed through the Turn event emitter.

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/card.py mtgengine/tests/test_game.py
git commit -m "feat: add perform_play_land helper"
```

### Task 11 (PR-11): Implement `_handle_first_main_phase` event handler

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_first_main_phase_calls_play_land_if_available(mocker) -> None:
    game = seeded_game()
    play_land = mocker.patch.object(game, "perform_play_land", return_value=True)
    game.perform_first_main_phase()
    play_land.assert_called_once()
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_first_main_phase_calls_play_land_if_available -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_first_main_phase(self) -> None:
    self._emit_step_event(TurnPrecombatMainPhaseEvent)

def _handle_first_main_phase(self, event: TurnPrecombatMainPhaseEvent) -> None:
    self.perform_play_land()
    self.event_log.append({
        "type": "first_main_phase",
        "player_index": self.players.index(event.turn.active_player),
    })

# In Game.__init__:
EventLinker.on(TurnPrecombatMainPhaseEvent)(self._handle_first_main_phase)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add first-main-phase handler"
```

### Task 12 (PR-12): Implement `_handle_combat_phase` no-op

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_combat_phase_logs_noop() -> None:
    game = seeded_game()
    game.perform_combat_phase()
    assert game.event_log[-1]["type"] == "combat_phase"
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_combat_phase_logs_noop -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_combat_phase(self) -> None:
    self._emit_step_event(TurnCombatPhaseEvent)

def _handle_combat_phase(self, event: TurnCombatPhaseEvent) -> None:
    self.event_log.append({
        "type": "combat_phase",
        "player_index": self.players.index(event.turn.active_player),
    })

# In Game.__init__:
EventLinker.on(TurnCombatPhaseEvent)(self._handle_combat_phase)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add combat-phase no-op logging handler"
```

### Task 13 (PR-13): Implement `_handle_second_main_phase` no-op

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_second_main_phase_logs_noop() -> None:
    game = seeded_game()
    game.perform_second_main_phase()
    assert game.event_log[-1]["type"] == "second_main_phase"
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_second_main_phase_logs_noop -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_second_main_phase(self) -> None:
    self._emit_step_event(TurnPostcombatMainPhaseEvent)

def _handle_second_main_phase(self, event: TurnPostcombatMainPhaseEvent) -> None:
    self.event_log.append({
        "type": "second_main_phase",
        "player_index": self.players.index(event.turn.active_player),
    })

# In Game.__init__:
EventLinker.on(TurnPostcombatMainPhaseEvent)(self._handle_second_main_phase)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add second-main-phase no-op logging handler"
```

### Task 14 (PR-14): Implement `_handle_cleanup_step` no-op

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_perform_cleanup_step_logs_noop() -> None:
    game = seeded_game()
    game.perform_cleanup_step()
    assert game.event_log[-1]["type"] == "cleanup_step"
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_perform_cleanup_step_logs_noop -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def perform_cleanup_step(self) -> None:
    self._emit_step_event(TurnCleanupStepEvent)

def _handle_cleanup_step(self, event: TurnCleanupStepEvent) -> None:
    self.event_log.append({
        "type": "cleanup_step",
        "player_index": self.players.index(event.turn.active_player),
    })

# In Game.__init__:
EventLinker.on(TurnCleanupStepEvent)(self._handle_cleanup_step)
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add cleanup-step no-op logging handler"
```

### Task 15 (PR-15): Implement `advance_to_next_player`

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing tests**
```python
def test_advance_to_next_player_switches_active_player() -> None:
    game = seeded_game()  # starts with game.turn = Turn(1, game.players[0])
    game.advance_to_next_player()
    assert game.turn.active_player is game.players[1]
    assert game.turn.turn_number == 1

def test_advance_to_next_player_wraps_and_increments_turn_cycle() -> None:
    game = seeded_game()
    game.turn = Turn(1, game.players[1])
    game.advance_to_next_player()
    assert game.turn.active_player is game.players[0]
    assert game.turn.turn_number == 2
```

- [ ] **Step 2: Run tests to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_advance_to_next_player_switches_active_player mtgengine/tests/test_game.py::test_advance_to_next_player_wraps_and_increments_turn_cycle -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def advance_to_next_player(self) -> None:
    current_index = self.players.index(self.turn.active_player)
    if current_index == len(self.players) - 1:
        self.turn = Turn(self.turn.turn_number + 1, self.players[0])
    else:
        self.turn = Turn(self.turn.turn_number, self.players[current_index + 1])
```
This replaces `self.turn` wholesale rather than mutating a stored index; `Turn` remains the single source of truth for turn number and active player.

- [ ] **Step 4: Re-run tests**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add cycle-based active-player advancement"
```

### Task 16 (PR-16): Implement `advance_turn` orchestration

**Files:**
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing test**
```python
def test_advance_turn_runs_full_turn_pipeline(mocker) -> None:
    game = seeded_game()
    beginning = mocker.patch.object(game, "perform_beginning_phase")
    main1 = mocker.patch.object(game, "perform_first_main_phase")
    combat = mocker.patch.object(game, "perform_combat_phase")
    main2 = mocker.patch.object(game, "perform_second_main_phase")
    cleanup = mocker.patch.object(game, "perform_cleanup_step")
    advance = mocker.patch.object(game, "advance_to_next_player")
    game.advance_turn()
    beginning.assert_called_once()
    main1.assert_called_once()
    combat.assert_called_once()
    main2.assert_called_once()
    cleanup.assert_called_once()
    advance.assert_called_once()
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_advance_turn_runs_full_turn_pipeline -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def advance_turn(self) -> None:
    if self.is_game_over:
        return
    self.perform_beginning_phase()
    if self.is_game_over:
        return
    self.perform_first_main_phase()
    self.perform_combat_phase()
    self.perform_second_main_phase()
    self.perform_cleanup_step()
    self.advance_to_next_player()
```

- [ ] **Step 4: Re-run test**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add full advance_turn orchestration"
```

### Task 17 (PR-17): Implement `snapshot`, `to_json`, `from_json`

**Files:**
- Create: `mtgengine/game_snapshot.py`
- Modify: `mtgengine/game.py`
- Test: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing tests**
```python
def test_snapshot_contains_shared_battlefield_and_owner_index() -> None:
    game = seeded_game()
    game.perform_play_land()
    snapshot = game.snapshot()
    assert "battlefield" in snapshot
    assert snapshot["battlefield"][-1]["owner_index"] == game.players.index(game.turn.active_player)

def test_json_round_trip_rebuilds_state() -> None:
    game = seeded_game()
    payload = game.to_json()
    rebuilt = Game.from_json(payload)
    assert rebuilt.snapshot() == game.snapshot()
```

- [ ] **Step 2: Run tests to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_snapshot_contains_shared_battlefield_and_owner_index mtgengine/tests/test_game.py::test_json_round_trip_rebuilds_state -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal code**
```python
def snapshot(self) -> dict[str, object]:
    return {
        "turn_number": self.turn.turn_number,
        "current_player_index": self.players.index(self.turn.active_player),
        "is_game_over": self.is_game_over,
        "winner_index": None if self.winner is None else self.players.index(self.winner),
        "players": [
            {
                "name": player.name,
                "deck": [card.name for card in player.deck.get_cards()],
                "hand": [card.name for card in player.hand.get_cards()],
                "graveyard": [card.name for card in player.graveyard.get_cards()],
                "exile": [card.name for card in player.exile.get_cards()],
            }
            for player in self.players
        ],
        "battlefield": [
            {
                "owner_index": card.owner_index,
                "card_name": card.name,
                "tapped": card.tapped,
            }
            for card in self.battlefield.get_cards()
        ],
        "event_log": self.event_log,
    }
```

- [ ] **Step 4: Re-run tests**
Run: same pytest command  
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add mtgengine/game_snapshot.py mtgengine/game.py mtgengine/tests/test_game.py
git commit -m "feat: add snapshot serialization and JSON round-trip"
```

### Task 18 (PR-18): Final integration tests for full game run-to-loss

**Files:**
- Modify: `mtgengine/tests/test_game.py`

- [ ] **Step 1: Write failing integration test**
```python
def test_full_mvp_game_ends_on_empty_library_draw() -> None:
    game = seeded_game_with_60_lands_each()
    game.start_game()
    while not game.is_game_over:
        game.advance_turn()
    assert game.winner is not None
    assert any(e["type"] == "lose_on_empty_library" for e in game.event_log)
```

- [ ] **Step 2: Run test to verify failure**
Run: `pytest mtgengine/tests/test_game.py::test_full_mvp_game_ends_on_empty_library_draw -v`  
Expected: FAIL

- [ ] **Step 3: Implement minimal fixups**
```python
# keep this PR test-focused; only add deterministic assertions and helpers in test code
def run_until_game_over(game: Game, max_turns: int = 200) -> None:
    for _ in range(max_turns):
        if game.is_game_over:
            return
        game.advance_turn()
    raise AssertionError("Game did not end within max_turns")
# discovered by the integration test
```

- [ ] **Step 4: Run target tests and then suite**
Run: `pytest mtgengine/tests/test_game.py -v`  
Expected: PASS  
Run: `make test`  
Expected: PASS with coverage output

- [ ] **Step 5: Commit**
```bash
git add mtgengine/tests/test_game.py mtgengine/game.py mtgengine/game_snapshot.py
git commit -m "test: verify end-to-end MVP game lifecycle to empty-library loss"
```

---

## Self-review checklist (completed)

- **Spec coverage:** Covered shared battlefield, indexed player references, deterministic player-0 start, `perform_*` method naming, separated draw/loss/play-land/main-phase PRs, cycle-based turn increment semantics, and snapshot persistence.
- **Placeholder scan:** Removed TBD/TODO placeholders from implementation tasks.  
- **Type consistency:** Kept `is_game_over`, `current_player_index` (derived, not stored), and `winner_index` naming consistent with the approved spec.

## Update log

- **2026-09-21:** `Game.current_player_index` was removed; active-player and turn-number tracking now live entirely on `Turn` (`game.turn.active_player`, `game.turn.turn_number`). Tasks 1-4 marked complete to match merged PRs, and Tasks 5-18 were rewritten to derive a player index via `self.players.index(self.turn.active_player)` wherever one is needed, and `advance_to_next_player` now replaces `self.turn` with a new `Turn` instead of mutating a stored index.
- **2026-09-21:** Folded in the event-emitter architecture actually used for `perform_beginning_phase`: each turn-phase/step `perform_*` method only emits its `Turn*Event` via `self._emit_step_event(...)`; rule behavior for untap/upkeep/draw/first-main/combat/second-main/cleanup now lives in paired `_handle_*` methods registered once in `Game.__init__` via `EventLinker.on(EventType)(self._handle_x)`. `perform_play_land()` remains a direct, non-event method since it's a player action rather than a turn-clock tick.
