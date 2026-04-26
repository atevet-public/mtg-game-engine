# Design: General Copilot Instructions

**Date:** 2026-04-26
**File to create:** `.github/copilot-instructions.md`

## Problem

The repository has no Copilot instruction file. Without one, AI assistants working in this codebase lack context about the MTG domain, the architecture philosophy, coding conventions, testing discipline, and workflow policies — leading to inconsistent code generation that may not follow established patterns.

## Approach

A structured, high-signal instruction file organized into six sections. Each section is concise and actionable. The goal is density of useful signal, not exhaustive documentation. Copilot should be able to scan any section quickly and find a clear directive.

## Sections

### 1. Project Purpose

A Python implementation of a Magic: The Gathering game engine. The architecture mirrors the structure of the MTG rules: zones, phases, the stack, permanents, abilities, and players. The Magic: The Gathering Comprehensive Rules document is the authoritative reference for game behavior and lives at `docs/MagicCompRules <date>.txt`.

### 2. Architecture Principles

Game engine structure arises from the rules, not from generic software abstractions. Key modules:

- `game.py` — top-level game state
- `player.py` — player state
- `zone/` — all zone types (battlefield, hand, library, graveyard, exile, stack)
- `permanent.py` — battlefield objects
- `stack_object.py` — spells and abilities on the stack
- `mana_pool.py` — per-player mana tracking
- `card_definition.py`, `card_repository.py` — card data layer
- `abilities/` — ability, cost, effect hierarchies; keyword abilities
- `turn.py` — turn/phase/step structure

When in doubt about how a game mechanic should behave, consult the comprehensive rules document.

### 3. Python Conventions

- **Dataclasses:** Use `frozen=True` unless the object requires mutation.
- **Docstrings:** All modules have a module-level docstring. Classes and public methods use Google-style docstrings.
- **Circular imports:** Use `from __future__ import annotations` at the top of each file, and guard cross-module type-only imports with `TYPE_CHECKING`.
- **Typing:** Use Python type annotations throughout. No untyped public APIs.
- **Comments:** Only comment code that needs clarification. Do not add redundant or obvious comments.

### 4. Testing Discipline

TDD: write tests before implementation. Tests live in:

- `mtgengine/tests/` for core modules
- `mtgengine/zone/tests/` for zone modules

All new code requires tests. PRs should not reduce coverage. Run the full test suite with `make test`.

### 5. Make Commands

| Command | Purpose |
|---|---|
| `make deps` | Install Python dependencies via uv |
| `make test` | Run test suite with coverage report |
| `make lint` | Ruff lint check + mypy type check |
| `make fix` | Auto-fix lint issues + black formatting |
| `make install-uv` | Install the uv package manager |

### 6. Workflow

- Feature work on a dedicated branch off `main`
- Use git worktrees (`.worktrees/`) for parallel feature development
- Open a PR; CI must pass (Quality Checks workflow)
- Squash merge into `main`
- No direct commits to `main`

## File Location

`.github/copilot-instructions.md`

## Out of Scope

- Detailed MTG rules explanations (the comp rules doc covers this)
- Per-file architecture documentation (handled by module docstrings)
- CI/CD configuration details
