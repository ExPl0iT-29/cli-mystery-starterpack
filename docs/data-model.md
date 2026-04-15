# Data Model And Scaffold Contract

## Purpose

This document explains the project shape that `cli-mystery-starter` generates and the
minimum contract enforced by `validate`.

## Package-Level Data Flow

The package has four main responsibilities:

1. read configuration
2. create the target directory structure
3. write templated starter files
4. validate required paths and a small number of content invariants

## Configuration Model

`scaffold.py` starts from an internal default config and optionally overlays values from
an external JSON file.

### Default Config Fields

- `project_name`: slug source for the scaffolded project identity
- `display_title`: human-readable title used in generated files
- `theme`: author-facing story theme seed
- `player_role`: intended player fantasy or role
- `answer_type`: kind of final answer the mystery expects
- `clue_marker`: marker inserted into the opening incident file
- `folders`: directory list to create during scaffold

## Generated Directories

By default, `init` creates these folders:

- `game/interviews`
- `game/locations`
- `game/memberships`
- `game/logs`
- `game/registry`
- `hints`
- `docs`
- `design`
- `tools`

These directories represent a mix of:

- player-facing puzzle data
- author-facing design artifacts
- optional tooling support

## Generated Files

The scaffold writes a fixed starter set:

- `README.md`
- `instructions`
- `solution`
- `encoded`
- `game/incident`
- `game/people`
- `game/locations/East_Hall`
- `game/locations/North_Wing`
- `game/locations/South_Annex`
- `hints/hint1`
- `hints/hint2`
- `hints/hint3`
- `hints/hint4`
- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`
- `docs/notes.md`
- `tools/README.md`
- `mystery_config.json`

## Logical Artifact Roles

### Root Files

- `README.md`: high-level project entry point
- `instructions`: player-facing start file
- `solution`: answer verification instructions
- `encoded`: stored answer hash placeholder
- `mystery_config.json`: persisted scaffold config

### `game/`

This is the puzzle surface for players.

- `incident`: opening narrative and first clue pivots
- `people`: identity index with lookup targets
- `locations/`: location files used for line-based or file-based lookups
- `interviews/`, `memberships/`, `logs/`, `registry/`: additional evidence families

### `design/`

This is the authoring control surface.

- `story_bible.md`: hidden truth, motive, and evidence planning
- `clue_graph.md`: intended solve path and evidence dependencies

### `docs/`

This is project-specific author documentation inside a scaffolded game.

- `data_schemas.md`: per-dataset schema notes
- `notes.md`: freeform author notes

### `tools/`

Reserved for optional author tooling such as generators, checkers, or release helpers.

## Validation Contract

`validation.py` enforces a deliberately small set of checks.

### Required Paths

Validation fails if any of these are missing:

- `README.md`
- `instructions`
- `solution`
- `encoded`
- `game/incident`
- `game/people`
- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`

### Config-Aware Check

If `mystery_config.json` exists and parses successfully, validation checks that
`game/incident` contains the configured `clue_marker`.

### `game/people` Check

Validation expects `game/people` to contain:

- at least one header line
- at least one data record

This is a minimal sanity check, not full schema validation.

## Template Assumptions

The templates encode several authoring assumptions:

- clue discovery starts in `game/incident`
- the project uses a visible clue marker
- a `people` index connects names to next-step lookups
- answer verification is hash-based by default
- authors will maintain separate design artifacts from game data

## Important Limitations

The current contract does not validate:

- schema consistency across evidence families
- whether the mystery has exactly one valid solution
- whether hints align with the real clue graph
- whether `encoded` matches the intended answer
- whether generated filler data contradicts the story bible

That means maintainers should treat the current validator as a smoke test, not as a
completeness gate.

## Maintenance Guidance

When changing the scaffold, keep these layers aligned:

1. default config in `scaffold.py`
2. file templates in `templates.py`
3. required paths and invariants in `validation.py`
4. package README and docs

If one changes without the others, authors will get a misleading scaffold.

## Bottom Line

The starter pack defines a lightweight project contract: enough structure to create a
usable mystery repo, but intentionally not enough automation to replace real puzzle
design.
