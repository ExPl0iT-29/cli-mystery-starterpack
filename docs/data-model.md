# Data Model And Scaffold Contract

## Purpose

This document explains the project shape that `cli-mystery-starter` generates and the
minimum contract enforced by `validate`.

## Package-Level Data Flow

The package has four main responsibilities:

1. read configuration
2. create the target directory structure
3. write templated starter files
4. validate project compatibility and content invariants

## Configuration Model

`scaffold.py` starts from an internal default config and optionally overlays values from
an external JSON file.

### Default Config Fields

The schema is enforced by `MysteryConfig` in `config.py`:

- `contract_version`: integer; bumped when the on-disk shape changes
- `project_name`: slug source for the scaffolded project identity
- `display_title`: human-readable title used in generated files
- `theme`: author-facing story theme seed
- `player_role`: intended player fantasy or role
- `answer_format`: `sha256_salted` (default) or `md5_legacy`
- `clue_marker`: marker inserted into the opening incident file
- `hint_count`: number of progressive hints (default 4)
- `folders`: directory list to create during scaffold

Unknown keys raise on load. `..` and absolute paths are rejected in
`folders`. The legacy `answer_type` field has been removed.

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
- `play.py`
- `game/incident`
- `game/people`
- `game/interviews/README.md`
- `game/locations/East_Hall`
- `game/locations/North_Wing`
- `game/locations/South_Annex`
- `game/memberships/README.md`
- `game/logs/README.md`
- `game/registry/README.md`
- `hints/hint1`
- `hints/hint2`
- `hints/hint3`
- `hints/hint4`
- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`
- `docs/notes.md`
- `tools/README.md`
- `tools/check_answer.py`
- `mystery_config.json`

## Logical Artifact Roles

### Root Files

- `README.md`: high-level project entry point
- `instructions`: player-facing start file
- `solution`: answer verification instructions
- `encoded`: stored answer hash placeholder
- `play.py`: thin runtime entry point into the starter package
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
The scaffold seeds `tools/check_answer.py` as a thin wrapper around the package helper.

## Validation Contract

`validation.py` enforces the starter-pack compatibility contract.

### Required Paths

Validation fails if any of these are missing:

- `README.md`
- `instructions`
- `solution`
- `encoded`
- `play.py`
- `game/incident`
- `game/people`
- `hints/hint1`
- `hints/hint2`
- `hints/hint3`
- `hints/hint4`
- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`
- `tools/check_answer.py`

### Config-Aware Check

If `mystery_config.json` exists and parses successfully, validation checks that:

- `game/incident` contains the configured `clue_marker`
- the incident contains at least three clue markers
- configured folders exist

### `game/people` Check

Validation expects `game/people` to contain:

- at least one header line
- at least one data record
- a header that uses either `|` or tab delimiters

### Additional Checks

Validation also checks:

- `encoded` matches the answer-format envelope declared by
  `answer_format` (`sha256_salted` envelope or 32-char `md5_legacy`)
- `encoded` is **not** still the default `John Doe` placeholder hash
  when `project_name` is also unchanged
- evidence-family directories contain at least one file
- `play.py` calls the package runtime helper
- `tools/check_answer.py` calls the package answer helper
- structural shape of every optional subsystem when its file exists:
  `game/clues.json`, `solutions.json`, `game/dialogue/*.json`,
  `game/scenes.json` (each surfaces parse and field errors)

This is a sanity gate, not a uniqueness/fairness proof. For
"does the evidence narrow to one suspect?" run
`cli-mystery-starter check-solve <project>` separately (see §below).

## Template Assumptions

The templates encode several authoring assumptions:

- clue discovery starts in `game/incident`
- the project uses a visible clue marker
- a `people` index connects names to next-step lookups
- answer verification is salted-SHA-256 by default (`md5_legacy`
  available for backward compatibility, with `usedforsecurity=False`
  on FIPS-strict hosts)
- authors will maintain separate design artifacts from game data
- optional subsystems (clues / solutions / dialogue / scenes) are
  data-driven add-ons, never edits to the package source

## Optional Subsystem Schemas

Each subsystem activates when its file exists; otherwise the runtime
behaves as it did on day one. Validation surfaces structural errors
when present.

### `game/clues.json`

Top-level: array of clue objects.

```json
[
  {
    "id": "ledger_44",                              // unique slug, required
    "title": "Mismatched signature in the ledger",  // required
    "source_path": "game/registry/ledger.txt",      // path beneath project root, required
    "tags": ["timeline", "points:maria_ortega"]     // strings; `points:<slug>` and
                                                    // `exonerates:<slug>` participate
                                                    // in the uniqueness solver
  }
]
```

Player effect: when `cat <source_path>` runs, the clue is auto-marked
discovered and `clue:revealed` fires on the event bus. Discovered ids
persist in `.session.json`.

### `solutions.json` (project root)

Top-level: object with `answers` and optional `endings`.

```json
{
  "answers": {
    "<field-name>": {
      "value": "<canonical answer>",            // required, non-empty
      "aliases": ["alt 1", "alt 2"]              // optional list of strings
    }
  },
  "endings": [
    {
      "id": "<ending-id>",                       // required, unique
      "requires": ["<field-name>", "..."],       // every name must be in `answers`
      "text": "<narration printed on this ending>"
    }
  ]
}
```

Field matching is case-insensitive and whitespace-collapsing;
aliases broaden acceptance. `endings` is evaluated in declared order;
the first whose `requires` are all matched fires. If `endings` is
omitted, a default `solve` ending requiring every answer field is
synthesized. When `solutions.json` is absent the runtime falls back
to the legacy `encoded` flow.

### `game/dialogue/<slug>.json`

One file per NPC. The filename stem (lowercased) becomes the slug
players use after `ask`.

```json
{
  "name": "The Butler",                            // optional, defaults to slug
  "greeting": "I served the family for thirty years.",
  "topics": [
    {
      "id": "chandelier",                          // required, unique within file
      "summary": "the chandelier",                 // shown by `ask <npc>`
      "response": "I oiled it last Tuesday.",      // required, printed on ask
      "requires_clues": [],                        // gate: every id must be discovered
      "reveals_clue": "butler_alibi_break"         // optional; auto-marks on first ask
    }
  ]
}
```

### `game/scenes.json`

Top-level: object with `start` (id) and `scenes` (array).

```json
{
  "start": "discover",
  "scenes": [
    {
      "id": "discover",                            // required, unique
      "narration": "...",                          // printed on entry
      "advances_to": "confront",                   // string id or null (final)
      "advance_when": {                            // every listed predicate must hold
        "files_read":      ["game/incident"],
        "clues":           [],
        "suspects_marked": [],
        "topics_asked":    []
      }
    }
  ]
}
```

`advances_to: null` marks a final scene. `topics_asked` entries are
strings of the form `"<npc>:<topic>"`. Current scene persists in
`.session.json`.

## Uniqueness Verdict (`check-solve`)

`solver.py` combines `game/clues.json` + `solutions.json` to produce
one of:

| Verdict        | Meaning |
|----------------|---|
| `UNIQUE`       | One strict top scorer, matches canonical culprit |
| `AMBIGUOUS`    | Two or more suspects tie at the top |
| `MISMATCH`     | Top scorer is not the canonical culprit |
| `INSUFFICIENT` | Missing files or no `points:` / `exonerates:` tags |
| `ERROR`        | Structural problems block analysis |

Score = `#points - #exonerates`, computed across every suspect from
column 1 of `game/people`. Slugs use lowercase + spaces-to-underscores
normalization (e.g., `Maria Ortega` → `maria_ortega`).

## Important Limitations

What validation **still** does not prove:

- semantic consistency across evidence families
- whether hints align with the real clue graph
- whether generated filler data contradicts the story bible

`check-solve` covers uniqueness when authors annotate clues with
directional tags, but cannot synthesize evidence or detect prose
contradictions. Treat the validator + solver as compatibility +
fair-play gates, not a fairness proof.

## Maintenance Guidance

When changing the scaffold, keep these layers aligned:

1. `contract.py` — single source of truth (drives scaffold, validation, runtime surfaces)
2. file templates in `templates.py`
3. `config.py` schema if a config field changes
4. `verifier.py` if the answer format changes
5. package README and docs

`contract.py` is intentionally the only place to edit when adding a
required file or evidence family. If one of the other layers drifts
without a contract update, authors will get a misleading scaffold.

## Bottom Line

The starter pack defines a lightweight project contract: enough structure to create a
usable mystery repo, but intentionally not enough automation to replace real puzzle
design.
