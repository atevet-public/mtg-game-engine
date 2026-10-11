"""Tests for interactive CLI server selection and --join shorthand."""

from pathlib import Path
from typing import Any

from mtgengine.server import cli


def test_play_resolves_server_from_argument_environment_and_default(monkeypatch: Any) -> None:
    calls: list[tuple[str, Path | None]] = []
    monkeypatch.setattr(
        cli, "run_play_session", lambda server, join_path=None: calls.append((server, join_path))
    )
    monkeypatch.setenv("MTGTABLE_SERVER", "http://env.test")

    cli.main(["play"])
    cli.main(["play", "--server", "http://flag.test", "--join", "alice.json"])
    monkeypatch.delenv("MTGTABLE_SERVER")
    cli.main(["play"])

    assert calls == [
        ("http://env.test", None),
        ("http://flag.test", Path("alice.json")),
        ("http://127.0.0.1:8000", None),
    ]
