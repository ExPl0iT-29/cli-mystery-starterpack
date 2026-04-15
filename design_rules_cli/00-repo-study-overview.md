# Repo Study Overview

## Study Goal

This document explains what `clmystery` is doing well at a system level, so future CLI mystery games can preserve the strengths and avoid copying only the surface aesthetics.

## High-Level Read

`clmystery` is a static, file-backed mystery game that teaches shell usage by making the player operate as a detective over a simulated evidence corpus.

It succeeds because it aligns:

- story goal: solve a murder
- interaction model: inspect files with shell commands
- data model: records split across folders and files
- learning model: clues force the use of `grep`, `head`, `tail`, `cat`, `cd`, and pipes

## What Exists In The Repo

Observed repo shape:

- root-level onboarding files
- one main game subtree: `mystery/`
- 661 files under `mystery/`
- 681 files total in the repo during study
- about 5.0 MB of text-heavy content

Observed primary data files:

- `mystery/crimescene`
- `mystery/people`
- `mystery/vehicles`
- `mystery/interviews/` with 425 files
- `mystery/memberships/` with 11 files
- `mystery/streets/` with 222 files

Observed scale properties:

- `people` has 5,028 lines
- `vehicles` has 30,129 lines
- `crimescene` has 9,390 lines
- every `streets/*` file has exactly 300 lines
- membership files each contain roughly 1,200 to 1,300 names

Those numbers matter. They show that the game is designed around realistic search volume, not tiny handcrafted toy files.

## Why The Design Works

The design works because the player never feels like they are solving an abstract puzzle. They feel like they are performing investigation work.

The repo produces that feeling by combining:

- large noisy files
- sparse meaningful signals
- natural pivots between datasets
- progressive hints
- lightweight thematic writing

The mystery remains playable because the noise is structured rather than random.

## The Hidden Structural Pattern

At a deeper level, the game is built from six layers:

1. onboarding
2. starter evidence
3. person lookup
4. location lookup
5. supporting evidence systems
6. answer verification

That is the transferable pattern, more than the specific murder story.

## View From Three Disciplines

### Game Dev View

This is a systems puzzle with narrative framing. The player loop is search, infer, pivot, confirm.

### Coder View

This is a static data architecture with optional tooling potential. The shell is the runtime interface.

### Writer View

This is a sparse narrative frame around procedural discovery. The text is there to direct attention and sustain mood, not dominate screen time.

## What To Reuse

Reuse these design ideas:

- filesystem as world
- one clear starting file
- multiple evidence domains
- noise with structure
- clue graph over brute-force reading
- progressive hints
- hidden answer verification

Do not blindly reuse:

- murder theme
- exact folder names
- exact clue marker words
- exact pacing of the original

The structure is reusable. The surface fiction should change.
