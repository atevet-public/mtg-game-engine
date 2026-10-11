"""Command-line entry point for running the MTGTable server."""

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from mtgengine.client.session import run_play_session
from mtgengine.server.app import create_app

DEFAULT_SERVER = "http://127.0.0.1:8000"


def main(arguments: Sequence[str] | None = None) -> None:
    """Run the server or interactive client subcommand.

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
    play = commands.add_parser("play", help="play through the interactive HTTP client")
    play.add_argument("--server")
    play.add_argument("--join", type=Path)
    options = parser.parse_args(arguments)
    if options.command == "serve":
        if options.players != 2:
            parser.error("the server currently supports only --players 2")
        uvicorn.run(
            create_app(expected_players=options.players),
            host=options.host,
            port=options.port,
            workers=1,
        )
        return
    server = options.server or os.environ.get("MTGTABLE_SERVER") or DEFAULT_SERVER
    run_play_session(server, join_path=options.join)
