# Project Overview

## What This Repository Is

This workspace is a starter pack for building filesystem-based CLI mystery games.
Its main deliverable is the Python package in `cli_mystery_starter/`, which exposes a
small command-line interface for creating, validating, playtesting, and verifying new
mystery projects.

The repository also contains:

- `docs/`: documentation for the starter pack
- `design_rules_cli/`: reusable design-study material extracted from the original CLI mystery pattern

## What The Package Does

The package supports five core workflows:

1. `init`: scaffold a new mystery project from templates
2. `validate`: run scaffold and content-contract checks against an authored project
3. `play`: locally run a project in the reusable investigation shell
4. `check-answer`: verify a suspect name against the encoded solution
5. `check-solve`: heuristic uniqueness check on the clue graph
   (UNIQUE / AMBIGUOUS / MISMATCH / INSUFFICIENT)

This makes the repository an authoring and development tool, not a packaged game in
itself.

## Primary Users

### Mystery Author

The author uses the starter pack to create a new project, then fills in the generated
story, clue graph, game data, and hints.

### Maintainer

The maintainer updates templates, config defaults, validation logic, and package-level
documentation so authors get a coherent starting point.

## Repository Layout

```text
E:\cli mystery starter pack
├─ cli_mystery_starter/
│  ├─ pyproject.toml
│  ├─ README.md
│  ├─ examples/
│  └─ src/cli_mystery_starter/
├─ docs/
└─ design_rules_cli/
```

## Package Layout

The package implementation is small but layered:

Core (always loaded):
- `cli.py`: argument parsing and command dispatch
- `contract.py`: single source of truth for the project shape
- `config.py`: typed `MysteryConfig` schema + loader
- `scaffold.py`: config-validated file generation
- `templates.py`: text templates for generated files
- `validation.py`: project-contract checks
- `verifier.py`: answer-format envelope (sha256_salted, md5_legacy)
- `answer.py`: answer verification helper
- `runtime.py`: reusable investigation shell
- `events.py`: in-process event bus
- `session.py`: `.session.json` persistence

Optional subsystems (only active when their data file exists):
- `clues.py`: clue object model + `clues` verb
- `solutions.py`: multi-field, multi-ending answers
- `dialogue.py`: NPC dialogue + `ask` verb
- `scenes.py`: scene/beat engine + `scene` verb
- `solver.py`: heuristic uniqueness verdict for `check-solve`

## CLI Surface

### Initialize A Project

Create a new mystery scaffold:

```bash
python -m cli_mystery_starter init my-mystery
```

Optional custom configuration:

```bash
python -m cli_mystery_starter init my-mystery --config mystery_config.json
```

### Validate A Project

Run the built-in validation pass against an authored project:

```bash
python dev.py validate my-mystery
```

### Playtest A Project

Run the reusable investigation shell against an authored project:

```bash
python dev.py play my-mystery
```

### Check An Answer

Verify a suspect name against a project:

```bash
python dev.py check-answer my-mystery "John Doe"
```

### Check Solve Uniqueness

Confirm the clue graph narrows to exactly one suspect:

```bash
python dev.py check-solve my-mystery
```

Returns `UNIQUE`, `AMBIGUOUS`, `MISMATCH`, `INSUFFICIENT`, or `ERROR`.

## Generated Project Shape

The scaffold creates a project with these main areas:

- `game/`: puzzle-facing evidence and records
- `design/`: author-facing truth and clue-graph artifacts
- `docs/`: project-specific author notes and schemas
- `hints/`: progressive player hints
- `tools/`: optional generators and validators

It also creates root files such as `README.md`, `instructions`, `solution`, `encoded`,
and `mystery_config.json`.

## Design Intent

The starter pack assumes a specific game model:

- the filesystem is part of the play surface
- clues are followed through shell commands rather than a GUI
- authored content matters more than runtime code
- code exists mainly to scaffold, validate, and optionally generate content

## Optional Subsystems

Drop a JSON file in to unlock a subsystem; absence falls back to the
day-1 behavior:

| File | Subsystem |
|---|---|
| `game/clues.json`            | Structured clue registry, auto-discovery, `clues` verb |
| `solutions.json`             | Multi-field accusations, partial endings, alias matching |
| `game/dialogue/<npc>.json`   | NPC dialogue with clue-gated topics, `ask` verb |
| `game/scenes.json`           | Scene/beat pacing with predicate gates, `scene` verb |

Every subsystem subscribes to a runtime event bus
(`file:read`, `clue:revealed`, `suspect:marked`, `dialogue:asked`,
`scene:advanced`, `accuse:attempt`, …). Author your own custom
mechanic the same way (worked example in
[`developer-guide.md`](./developer-guide.md)).

## Constraints And Non-Goals

The starter pack still does not provide:

- advanced puzzle balancing
- content-generation pipelines for evidence families
- non-English localization hooks
- a graphical UI of any kind

These are deliberate omissions; the pack is optimized for simple,
portable, text-first mystery projects.

## Recommended Reading Order For New Maintainers

1. Read [`cli_mystery_starter/README.md`](../cli_mystery_starter/README.md).
2. Review [`data-model.md`](./data-model.md) for scaffold and validation details.
3. Review [`designing-cli-mystery-games.md`](./designing-cli-mystery-games.md) for the authoring assumptions baked into the templates.

## Bottom Line

Describe this repository as:

`cli-mystery-starter` is a Python authoring tool that scaffolds, validates, and locally
playtests filesystem-based command-line mystery games.
