"""Mana pool for tracking floating mana."""

from collections import defaultdict

MANA_COLORS = frozenset({"W", "U", "B", "R", "G", "C"})


class ManaPool:
    """Tracks floating mana available to a player."""

    def __init__(self) -> None:
        """Initialize an empty mana pool."""
        self._mana: defaultdict[str, int] = defaultdict(int)

    def add(self, color: str, amount: int = 1) -> None:
        """Add mana of the given color. Color must be W/U/B/R/G/C or 'generic'.

        Args:
            color: Mana color (W/U/B/R/G/C or 'generic').
            amount: Amount of mana to add (default: 1).

        Raises:
            ValueError: If color is invalid or amount is less than 1.
        """
        if color not in MANA_COLORS and color != "generic":
            raise ValueError(f"Invalid mana color: {color}")
        if amount < 1:
            raise ValueError("Amount must be at least 1")
        self._mana[color] += amount

    def available(self, color: str) -> int:
        """Return available mana of the given color.

        Args:
            color: Mana color to query.

        Returns:
            Amount of mana available of that color.

        Raises:
            ValueError: If color is invalid.
        """
        if color not in MANA_COLORS and color != "generic":
            raise ValueError(f"Invalid mana color: {color}")
        return self._mana.get(color, 0)

    def total(self) -> int:
        """Return total floating mana.

        Returns:
            Total amount of mana in the pool.
        """
        return sum(self._mana.values())

    def empty(self) -> None:
        """Empty the mana pool (called at end of each step/phase)."""
        self._mana.clear()

    def spend(self, color: str, amount: int = 1) -> bool:
        """Spend mana of the given color. Returns True on success, False if insufficient.

        Does not partially spend — either all or nothing.

        Args:
            color: Mana color to spend.
            amount: Amount of mana to spend (default: 1).

        Returns:
            True if mana was spent successfully, False if insufficient mana.

        Raises:
            ValueError: If color is invalid or amount is less than 1.
        """
        if color not in MANA_COLORS and color != "generic":
            raise ValueError(f"Invalid mana color: {color}")
        if amount < 1:
            raise ValueError("Amount must be at least 1")
        if self._mana.get(color, 0) < amount:
            return False
        self._mana[color] -= amount
        if self._mana[color] == 0:
            del self._mana[color]
        return True

    def __repr__(self) -> str:
        """Return string representation of the mana pool.

        Returns:
            String representation showing mana contents.
        """
        return f"ManaPool({self._mana})"
