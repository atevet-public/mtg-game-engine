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
The record of Players who have lost; when the game ends, it also contains the winner, ending Turn Number, and reason.
_Avoid_: Outcome, score

**Empty-Library Loss**:
The loss suffered by a player who attempts to draw from an empty deck.
_Avoid_: Decking, milled out

**Maximum Hand Size**:
The number of cards a player may hold at cleanup; normally seven.
_Avoid_: Hand limit

**Move**:
A player command that advances the game by exactly one step or phase.
_Avoid_: Next, advance

**Pass**:
A player command that advances through every remaining step and phase of the Active Player's turn.  It stops for a required player decision, such as discarding to hand size, or at the next Active Player's first main phase; every step and phase passed through still occurs.  Pass turn does not stop for optional player decisions, like playing a land for the turn.
_Avoid_: End turn, skip

**MTGTable**:
The whole interactive system that lets people play a game of the engine: one shared game and one seat per participant.
_Avoid_: Platform, app

**Seat**:
A fixed position in a game occupied by one participant, numbered in join order; turn order follows seat order.
_Avoid_: Slot, player number
