"""ManaCost class representing a Magic: The Gathering mana cost."""

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ManaCost:
    """Represents a Magic: The Gathering mana cost."""

    white: int = 0
    blue: int = 0
    black: int = 0
    red: int = 0
    green: int = 0
    colorless: int = 0
    generic: int = 0

    def __post_init__(self) -> None:
        """Validate that all costs are non-negative."""
        if any(
            cost < 0
            for cost in [
                self.white,
                self.blue,
                self.black,
                self.red,
                self.green,
                self.colorless,
                self.generic,
            ]
        ):
            raise ValueError("Mana costs cannot be negative")

    @classmethod
    def from_notation(cls, notation: str) -> "ManaCost":
        """Parse mana cost from notation string.

        Examples:
            "2WUB" -> 2 generic, 1 white, 1 blue, 1 black
            "WW" -> 2 white
            "5" -> 5 generic
            "1CC" -> 1 generic, 2 colorless
            "" -> 0 total cost

        Args:
            notation: Mana cost notation string.

        Returns:
            ManaCost instance.

        Raises:
            ValueError: If notation contains invalid characters.
        """
        colors: dict[str, int] = defaultdict(int)
        num_str = ""

        for char in notation:
            if char.isdigit():
                num_str += char
            elif char in "WUBRGC":
                colors[char] += 1
            else:
                raise ValueError(f"Invalid mana notation character: {char}")

        return cls(
            white=colors["W"],
            blue=colors["U"],
            black=colors["B"],
            red=colors["R"],
            green=colors["G"],
            colorless=colors["C"],
            generic=int(num_str) if num_str else 0,
        )

    def mana_value(self) -> int:
        """Return the mana value of this cost.

        Returns:
            Sum of all mana costs.
        """
        return (
            self.white
            + self.blue
            + self.black
            + self.red
            + self.green
            + self.colorless
            + self.generic
        )
