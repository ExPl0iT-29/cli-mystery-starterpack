# Game Design Study

## Core Player Loop

From a game design perspective, `clmystery` is a deduction game with shell commands as mechanics.

The loop is:

1. receive lead
2. inspect evidence
3. derive suspect set
4. pivot into another evidence system
5. reduce uncertainty
6. confirm the final answer

This is good design because each step changes the information state of the player.

## Mechanics Hidden Inside Shell Usage

The shell commands are not just controls. They are the game mechanics.

- `ls` is exploration
- `cd` is traversal
- `cat` is evidence inspection
- `grep` is clue extraction
- `head` and `tail` are precision slicing
- pipes are compound reasoning

That means the command vocabulary must be treated as part of difficulty design.

## Difficulty Model

The game’s difficulty comes from four sources:

- scale of the data
- amount of irrelevant noise
- number of required pivots
- player familiarity with shell operations

It does not rely on twitch skill, hidden UI affordances, or timing. This makes it portable and durable.

## Progression Design

The progression is well controlled:

- first clue source is explicit
- early command use is simple
- later steps require combining evidence types
- hints reveal method before answer

This is effectively tutorialized investigation design.

## Puzzle Topology

The puzzle is neither fully linear nor fully open.

It is best described as guided branching:

- one starting node
- a few obvious mid-game branches
- a narrowing funnel near the end

That shape is ideal for beginner and intermediate players. A fully open evidence sandbox would be harder to parse and easier to break.

## Why The Street Files Are Strong Design

The street files are one of the smartest mechanics in the repo.

Why they work:

- they force precision
- they create a spatial fiction without a map UI
- wrong lines return gibberish, which acts as feedback
- they teach line-based slicing naturally

They are an example of puzzle friction that feels fair.

## Why The Membership Files Are Strong Design

The membership files create set intersection gameplay.

This is elegant because:

- the rule is intuitive
- the files are large enough to matter
- the player can solve it with simple shell operations
- the evidence feels diegetic

This is a strong pattern to reuse in future games: organizations, factions, subscriptions, manifests, or access groups.

## Hint System Design

The hint ladder is well paced:

- early hints teach the relevant command
- mid hints identify the right file family
- late hints explain the transformation or combination step

This is a better design than giving purely narrative hints. The player needs operational help, not just story nudges.

## Pacing

The repo uses a good rhythm:

- broad search
- narrow lookup
- broad search
- narrow lookup

That alternation keeps the investigation from feeling repetitive.

## Design Risks In This Style

If you build more games like this, watch for these risks:

- too many dataset pivots
- too much filler before the first satisfying deduction
- command requirements that exceed the intended audience
- one trivial search shortcut breaking the puzzle
- late-game ambiguity with multiple valid suspects

## Game Design Takeaway

The reusable lesson is this:

Design the evidence flow first, then let the shell commands become the natural verbs that operate on that evidence.
