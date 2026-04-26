# Copilot Instructions

## Project Purpose

This is a Python implementation of a Magic: The Gathering game engine. The
architecture mirrors the structure of the MTG rules: zones, phases, the stack,
permanents, abilities, and players.

The Magic: The Gathering Comprehensive Rules document is the authoritative
reference for all game behavior. It lives at
`docs/MagicCompRules 20260227.txt`. When in doubt about how a game mechanic
should behave, consult the comp rules.

## Architecture Principles

Game engine structure arises from the rules, not from generic software
abstractions. Key modules:

- `game.py` — top-level game state
- `player.py` — player state
- `zone/` — all zone types (battlefield, hand, library, graveyard, exile, stack)
- `permanent.py` — battlefield objects
- `stack_object.py` — spells and abilities on the stack
- `mana_pool.py` — per-player mana tracking
- `card_definition.py`, `card_repository.py` — card data layer
- `abilities/` — ability, cost, effect hierarchies; keyword abilities
- `turn.py` — turn/phase/step structure

## Python Conventions

- **Dataclasses:** Use `frozen=True` unless the object requires mutation.
- **Docstrings:** All modules have a module-level docstring. Classes and public
  methods use Google-style docstrings.
- **Circular imports:** Use `from __future__ import annotations` at the top of
  each file, and guard cross-module type-only imports with `TYPE_CHECKING`.
- **Typing:** Use Python type annotations throughout. No untyped public APIs.
- **Comments:** Only comment code that needs clarification. Do not add
  redundant or obvious comments.
- **Clean Code:** Follow basic Clean Code principles — use descriptive names,
  keep functions short (approximately 4 lines), and each function should do one
  thing.

## Testing Discipline

TDD: write tests before implementation. Tests live in:

- `mtgengine/tests/` for core modules
- `mtgengine/zone/tests/` for zone modules

All new code requires tests. PRs should not reduce coverage.

## Make Commands

| Command           | Purpose                              |
|-------------------|--------------------------------------|
| `make deps`       | Install Python dependencies via uv   |
| `make test`       | Run test suite with coverage report  |
| `make lint`       | Ruff lint check + mypy type check    |
| `make fix`        | Auto-fix lint issues + black format  |
| `make install-uv` | Install the uv package manager       |

## Workflow

- Feature work on a dedicated branch off `main`
- Use git worktrees (`.worktrees/`) for parallel feature development
- Open a PR; CI must pass (Quality Checks workflow)
- Squash merge into `main`
- No direct commits to `main`
- PRs should be small and focused — one feature or rule per PR when reasonable.
  For example, when implementing keyword abilities, open one PR per ability
  rather than one PR for all abilities.
