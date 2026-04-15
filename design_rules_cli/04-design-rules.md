# Design Rules

## Non-Negotiable Rules

These are the rules future CLI mystery games should follow unless there is a strong reason to break them.

### 1. Filesystem Is Gameplay

The filesystem must be part of the game world, not just storage behind the game.

### 2. One Clear Starting Point

The player must always know the first file or folder to inspect.

### 3. Command Vocabulary Must Match Audience

Do not require commands beyond the player’s intended skill level.

### 4. Solve Path Must Require Cross-Referencing

No single file should trivially reveal the final answer.

### 5. Noise Must Be Structured

Filler content must resemble real data and support the fiction.

### 6. Every Important Reference Must Resolve

If one file points to a person, street, organization, room, or transcript, that target must exist and be coherent.

### 7. Hints Must Escalate Method First

Hints should first reveal the tool or file family before they reveal the answer.

### 8. Verification Must Be Separate

Answer checking should exist, but not spoil the puzzle during ordinary browsing.

### 9. Difficulty Must Come From Deduction

Do not replace deduction with arbitrary obscurity or shell trivia.

### 10. Theme Should Serve Structure

Pick themes that naturally generate searchable records.

## Good Patterns To Reuse

- incident file with marked clues
- people directory
- location lookup by line or room
- rosters for set intersection
- logs for timestamp corroboration
- transcripts for contradiction detection
- hidden answer hash or validator

## Patterns To Avoid

- requiring custom executables to play
- nonlinear chaos with no obvious first move
- clever filenames that are annoying to type
- too many unique schemas
- clues embedded only in poetic prose
- random filler disconnected from the fiction

## Rule For New Games

Before shipping, you should be able to answer yes to all of these:

- Can a new player start in under five minutes?
- Can the puzzle be solved with the documented commands?
- Is there one intended solution?
- Does each major file family justify its existence?
- Does every late clue feel earned by earlier work?

If not, the design is not ready.
