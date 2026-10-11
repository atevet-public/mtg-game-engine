"""Command-line entry point for running the MTGTable server."""

import argparse
from collections.abc import Sequence

import uvicorn

from mtgengine.server.app import create_app


def main(arguments: Sequence[str] | None = None) -> None:
    """Run the single-worker server after parsing the ``mtgtable serve`` command.

    Args:
        arguments: Optional command-line arguments; defaults to process arguments.
    """
    parser = argparse.ArgumentParser(prog="mtgtable")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser(
        "serve",
        help="start the in-memory two-player MTGTable server (one worker only)",
        description="Run one server worker; multiple workers do not share lobby state.",
    )
    serve.add_argument("--players", type=int, default=2)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    options = parser.parse_args(arguments)
    if options.players != 2:
        parser.error("the server currently supports only --players 2")
    uvicorn.run(
        create_app(expected_players=options.players),
        host=options.host,
        port=options.port,
        workers=1,
    )
