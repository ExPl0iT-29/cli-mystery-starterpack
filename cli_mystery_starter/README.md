# CLI Mystery Starter

A reusable Python starter pack for building, validating, and local-playtesting
filesystem-based CLI mystery games.

## What This Includes

- a Python package under `src/`
- CLI commands to scaffold, validate, play, and verify mystery projects
- stronger project validation for scaffold compatibility
- a reusable investigation shell for local author playtesting
- starter templates for:
  - `play.py`
  - `instructions`
  - hints
  - docs
  - game data folders
  - answer verification wrappers
- a sample design config file
- a root `dev.py` launcher for local development without editable install

## Recommended Use

From this directory during local development:

```bash
python dev.py init my-mystery
```

If the package is installed or your environment already exposes `cli_mystery_starter`,
the equivalent command is:

```bash
python -m cli_mystery_starter init my-mystery
```

Then author the game content:

- `design/story_bible.md`
- `design/clue_graph.md`
- `game/incident`
- `game/people`
- `game/interviews/`
- `game/locations/`
- `hints/`

Then playtest:

```bash
cd my-mystery
python play.py
```

## Structure

```text
cli_mystery_starter/
├─ dev.py
├─ pyproject.toml
├─ tests/
├─ src/
│  └─ cli_mystery_starter/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ answer.py
│     ├─ cli.py
│     ├─ contract.py        # single source of truth for project shape
│     ├─ config.py          # MysteryConfig dataclass + schema
│     ├─ verifier.py        # answer-format envelope (sha256_salted, md5_legacy)
│     ├─ events.py          # in-process event bus
│     ├─ session.py         # .session.json persistence
│     ├─ clues.py           # optional clue object model
│     ├─ solutions.py       # optional multi-field, multi-ending answers
│     ├─ dialogue.py        # optional NPC dialogue system
│     ├─ scenes.py          # optional scene/beat engine
│     ├─ solver.py          # heuristic uniqueness check
│     ├─ runtime.py
│     ├─ scaffold.py
│     ├─ validation.py
│     └─ templates.py
├─ examples/
│  └─ mystery_config.json
└─ README.md
```

## Commands

- `init <path>`: create a new mystery project scaffold
- `validate <path>`: run scaffold and content-contract checks against a project
- `play <path>`: run a project in the reusable investigation shell
- `check-answer <path> <guess>`: verify a suspect name against a project
- `check-solve <path>`: heuristic uniqueness check (UNIQUE / AMBIGUOUS / MISMATCH / INSUFFICIENT)

## Local Development

This repository uses a `src/` layout. For local development, use:

```bash
python dev.py <command> ...
```

Examples:

```bash
python dev.py init my-mystery
python dev.py validate my-mystery
python dev.py play my-mystery
python dev.py check-answer my-mystery "John Doe"
```

If you prefer direct module execution, set `PYTHONPATH=src` first or install the package
in editable mode.

## Validation Contract

Validation checks:

- required scaffold files and folders (driven by `contract.py`)
- presence of `play.py` and `tools/check_answer.py`
- valid `mystery_config.json` against the typed schema
- clue marker presence and minimum clue count in `game/incident`
- basic `game/people` structure
- `encoded` answer-format envelope (sha256_salted or md5_legacy)
- placeholder-answer detection (warns when default `John Doe` ships
  unmodified)
- wrapper integrity for runtime and answer-check helpers
- structural shape of every optional subsystem when present:
  `game/clues.json`, `solutions.json`, `game/dialogue/*.json`,
  `game/scenes.json`

For uniqueness ("does my evidence narrow to one suspect?") run
`cli-mystery-starter check-solve <project>` separately.

## Optional Subsystems

The runtime exposes an event bus (`file:read`, `clue:revealed`,
`suspect:marked`, `dialogue:asked`, `scene:advanced`,
`accuse:attempt`, …). Drop a JSON file in to unlock a subsystem:

| File | Subsystem |
|---|---|
| `game/clues.json`            | Structured clue registry + `clues` verb |
| `solutions.json`             | Multi-field accusations + partial endings |
| `game/dialogue/<npc>.json`   | NPC dialogue with clue-gated topics |
| `game/scenes.json`           | Scene/beat pacing with predicate gates |

See `../docs/developer-guide.md` for the full subsystem reference.

## Tests

Run the automated test suite from this directory:

```bash
python -m unittest discover -s tests
```

## Why Python

Python is a good fit for this style of project because it is strong at:

- content generation
- schema validation
- packaging
- text processing
- cross-platform author tooling
