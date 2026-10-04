# MTG Game Engine

A Python engine that simulates Magic: The Gathering games following the Comprehensive Rules.

## Language

**Player Specification**:
The input describing one participant of a game: a name and a decklist.
_Avoid_: Player config, player input

**Decklist**:
Text listing a deck as lines of quantity, card name, and optional set code and collector number.
_Avoid_: Deck file, deck string

**Deck**:
A player's ordered library of cards, built from a decklist.
_Avoid_: Library (except when quoting the rules)

**Starting Player**:
The player randomly chosen to take the first turn; they skip the draw step of their first turn.
_Avoid_: First player, player zero

**Active Player**:
The player whose turn it currently is.
_Avoid_: Current player

**Turn Number**:
The count of completed rounds plus one; it increments only after every player has taken a turn.
_Avoid_: Round number

**Land Drop**:
Playing a land from hand to the battlefield; allowed once per turn, during a main phase.
_Avoid_: Land play

**Basic Land**:
A land card with the Basic supertype and the land type matching its name: Plains, Island, Swamp, Mountain, or Forest.
_Avoid_: Basic, land card

**Game Result**:
The outcome of a finished game: the winner, the loser, the turn number, and the reason it ended.
_Avoid_: Outcome, score

**Empty-Library Loss**:
The loss suffered by a player who attempts to draw from an empty deck.
_Avoid_: Decking, milled out
