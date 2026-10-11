# MTG Game Engine

A Python engine for lands-only Magic: The Gathering games, with an in-process API and the MTGTable HTTP server/client.

## Quick start

Install `uv` first if it is not already available (`make install-uv`), then install the project and its development dependencies:

```sh
make deps
```

Start the two-seat server in one terminal:

```sh
uv run mtgtable serve --players 2
```

The default address is `http://127.0.0.1:8000`. The lobby and game live in server memory, so run one Uvicorn worker only. The server command enforces this; see [docs/mtgtable-server.md](docs/mtgtable-server.md).

Create one Player Specification JSON file per participant, for example `alice.json`:

```json
{
  "name": "Alice",
  "decklist": "60 Forest",
  "starting_life": 20
}
```

The `starting_life` field is optional and defaults to 20. `decklist` is text with one entry per line in the form `quantity card name`, such as:

```text
24 Forest
20 Island
16 Mountain
```

The current engine requires at least 60 cards and supports only basic lands: Plains, Island, Swamp, Mountain, and Forest. Set codes and collector numbers are also accepted, for example `24 Forest (M21) 280`.

In separate terminals, join both players:

```sh
uv run mtgtable play --server http://127.0.0.1:8000 --join alice.json
uv run mtgtable play --server http://127.0.0.1:8000 --join bob.json
```

Example session:

```text
mtgtable> list hand
Forest x4
Island x3
mtgtable> pass
Seat 0: beginning phase
Seat 0: untap step
Seat 0: upkeep step
Seat 0: draw step
Seat 0: first main phase
mtgtable> play Forest
Seat 0 played Forest.
mtgtable> pass
...turn events continue until the next decision point...
```

Each client receives a Seat-specific bearer token and prints game events as they arrive. Use `list hand` or `list game_state` to inspect state. `pass` advances to a decision point; when it stops in a main phase, use `play Forest` to make a Land Drop. Continue with `pass`. Other prompt commands include `move`, `discard <card>`, `list <zone>`, `rejoin`, `help`, and `quit`.

Tokens are saved per server under `~/.mtg-cli/`; use `rejoin` after reconnecting with the same server URL. The prompt remains open after game over so the final state can still be queried.

## Tests

Run the fast suite and static checks with `make test` and `make lint`. The real-process HTTP end-to-end test is marked `integration` and can be run separately with `make test-integration`.
