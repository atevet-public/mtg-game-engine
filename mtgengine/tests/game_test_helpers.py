"""Shared helpers for deterministic game tests."""

import random
from collections.abc import MutableSequence
from typing import Any


class SelectSecondPlayerRandom(random.Random):
    """Keep deck order unchanged and always select the second player."""

    def shuffle(self, values: MutableSequence[Any]) -> None:
        """Leave deck order unchanged for predictable assertions."""

    def _randbelow(self, n: int) -> int:
        """Select the last item in the sequence supplied to choice()."""
        return n - 1
