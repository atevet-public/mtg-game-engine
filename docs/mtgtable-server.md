# Running the MTGTable server

Install the project and its declared dependencies, then run `mtgtable serve --players 2`. The
server listens on `127.0.0.1:8000` by default; `--host` and `--port` override those values.

The lobby and Game are held in process memory and protected by one `asyncio.Lock`. Run exactly
one Uvicorn worker: worker processes do not share Seats, bearer tokens, or Game state.
