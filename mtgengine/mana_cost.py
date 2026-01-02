"""ManaCost class representing a Magic: The Gathering mana cost."""

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
        white = 0
        blue = 0
        black = 0
        red = 0
        green = 0
        colorless = 0
        generic = 0

        i = 0
        while i < len(notation):
            char = notation[i]
            if char.isdigit():
                # Parse numeric prefix (e.g., "2" in "2WUB")
                num_str = ""
                while i < len(notation) and notation[i].isdigit():
                    num_str += notation[i]
                    i += 1
                generic += int(num_str)
            elif char == "W":
                white += 1
                i += 1
            elif char == "U":
                blue += 1
                i += 1
            elif char == "B":
                black += 1
                i += 1
            elif char == "R":
                red += 1
                i += 1
            elif char == "G":
                green += 1
                i += 1
            elif char == "C":
                colorless += 1
                i += 1
            else:
                raise ValueError(f"Invalid mana notation character: {char}")

        return cls(
            white=white,
            blue=blue,
            black=black,
            red=red,
            green=green,
            colorless=colorless,
            generic=generic,
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
