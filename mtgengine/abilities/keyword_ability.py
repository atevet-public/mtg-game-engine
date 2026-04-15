"""Keyword abilities as an enumeration."""

from enum import Enum, auto


class KeywordAbility(Enum):
    """Keyword abilities defined in the Magic: The Gathering Comprehensive Rules."""

    # Evasion
    FLYING = auto()
    REACH = auto()
    SHADOW = auto()
    INTIMIDATE = auto()
    FEAR = auto()
    LANDWALK = auto()  # subtype variant; base keyword
    PROTECTION = auto()  # from [quality]; base keyword

    # Combat
    TRAMPLE = auto()
    FIRST_STRIKE = auto()
    DOUBLE_STRIKE = auto()
    DEATHTOUCH = auto()
    LIFELINK = auto()
    VIGILANCE = auto()
    HASTE = auto()
    MENACE = auto()
    INDESTRUCTIBLE = auto()

    # Other common
    FLASH = auto()
    HEXPROOF = auto()
    SHROUD = auto()
    DEFENDER = auto()
    WARD = auto()
    CONVOKE = auto()
    ABSORB = auto()
    ANNIHILATOR = auto()  # has N parameter
    AFFINITY = auto()
    CYCLING = auto()
    EQUIP = auto()
    FLASHBACK = auto()
    KICKER = auto()
    MODULAR = auto()
    MYRIAD = auto()
    PROVOKE = auto()
    RAMPAGE = auto()
    SCRY = auto()  # (for "scry N" on triggered abilities)
    STORM = auto()
    SUNBURST = auto()
    SUSPEND = auto()
    UNDYING = auto()
    PERSIST = auto()
    WITHER = auto()
    INFECT = auto()
    BATTLE_CRY = auto()
    BLOODTHIRST = auto()
    BUSHIDO = auto()  # has N parameter
    EXTORT = auto()
    BATTALION = auto()
    CIPHER = auto()
    EVOLVE = auto()
    EXALTED = auto()
    EXPLOIT = auto()
    FABRICATE = auto()
    MORBID = auto()
    OVERLOAD = auto()
    POPULATE = auto()
    PROLIFERATE = auto()
    RAID = auto()
    RENOWN = auto()
    REVOLT = auto()
    SCAVENGE = auto()
    SPECTACLE = auto()
    SURGE = auto()
    THRESHOLD = auto()
    CHAMPION = auto()
    HAUNT = auto()
    SOULSHIFT = auto()
    TRANSMUTE = auto()
    UNEARTH = auto()

    @classmethod
    def from_string(cls, name: str) -> "KeywordAbility":
        """Parse a keyword ability name (case-insensitive) to its enum value.

        Args:
            name: The keyword name, e.g. 'Flying', 'first strike', 'TRAMPLE'.

        Returns:
            The matching KeywordAbility enum value.

        Raises:
            ValueError: If the name is not a recognized keyword.
        """
        normalized = name.strip().upper().replace(" ", "_").replace("-", "_")
        try:
            return cls[normalized]
        except KeyError:
            raise ValueError(f"Unknown keyword ability: {name!r}")
