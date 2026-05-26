# CLI Mystery Starter Pack

`cli mystery starter pack` is a workspace for designing and shipping filesystem-based
CLI mystery games.

It contains three main parts:

- `cli_mystery_starter/`: the Python package that scaffolds, validates, playtests, and verifies new mystery projects
- `docs/`: documentation for the starter pack and its authoring model
- `design_rules_cli/`: reusable design-study material for CLI mystery game structure

## What This Repository Is For

Use this repository when you want to:

- create a new text-first mystery game played through shell commands
- scaffold the file and folder structure for that game quickly
- keep authoring artifacts such as story truth and clue graphs separate from puzzle data
- validate the project contract before sharing or shipping it
- locally playtest a project with a reusable investigation shell

This repository is an authoring toolchain and reference pack, not a finished game.

## Workspace Layout

```text
E:\cli mystery starter pack
├─ README.md
├─ .gitignore
├─ cli_mystery_starter/
│  ├─ pyproject.toml
│  ├─ README.md
│  ├─ examples/
│  └─ src/cli_mystery_starter/
├─ docs/
└─ design_rules_cli/
```

## The Python Package

The package lives in `cli_mystery_starter/` and exposes five commands:

- `init <path>`: create a new mystery scaffold
- `validate <path>`: run scaffold and content-contract checks
- `play <path>`: run a mystery project in the reusable investigation shell
- `check-answer <path> <guess>`: verify a suspect name against a project
- `check-solve <path>`: heuristic uniqueness check on the clue graph (UNIQUE / AMBIGUOUS / MISMATCH)

The generated project shape is centered around:

- `game/`: player-facing evidence and puzzle files
- `design/`: story truth and clue-graph planning
- `docs/`: project-specific author notes and schemas
- `hints/`: progressive player hints
- `tools/`: optional generators and validators

## Quick Start

From the package directory:

```bash
cd cli_mystery_starter
python dev.py init my-mystery
```

To validate an authored project:

```bash
python dev.py validate my-mystery
```

To locally playtest an authored project:

```bash
python dev.py play my-mystery
```

If you want to customize the scaffold metadata, pass a JSON config:

```bash
python dev.py init my-mystery --config examples/mystery_config.json
```

## Recommended Authoring Flow

Do not start by generating large amounts of filler content. Use this order:

1. define the hidden truth in `design/story_bible.md`
2. define the solve path in `design/clue_graph.md`
3. author the opening clues in `game/incident`
4. connect names and lookup targets in `game/people`
5. add supporting evidence families such as `locations`, `interviews`, `logs`, or `memberships`
6. write progressive hints
7. run `validate`
8. playtest the full mystery

## Documentation

Start with the workspace docs:

- [`docs/index.md`](./docs/index.md)
- [`docs/project-overview.md`](./docs/project-overview.md)
- [`docs/data-model.md`](./docs/data-model.md)
- [`docs/designing-cli-mystery-games.md`](./docs/designing-cli-mystery-games.md)

Then read the package-specific README:

- [`cli_mystery_starter/README.md`](./cli_mystery_starter/README.md)

## Design Notes

The starter pack assumes a specific style of game design:

- the filesystem is part of the gameplay surface
- shell commands are the primary player interaction model
- code supports authoring, validation, and local playtesting, rather than being the shipped game itself
- puzzle quality depends on clue design, not on runtime complexity

## Optional Subsystems (data-driven, no code edits)

Drop a JSON file in to unlock a subsystem. A scaffolded case without
any of these behaves exactly as before:

| File | Unlocks |
|---|---|
| `game/clues.json`            | `clues` verb, auto-discovery on `cat`, journal counts |
| `solutions.json`             | Multi-field `accuse culprit=… motive=… weapon=…`, partial endings |
| `game/dialogue/<npc>.json`   | `ask <npc> [about <topic>]` verb with clue-gated topics |
| `game/scenes.json`           | `scene` verb, paced narration, gate-based transitions |
| (combo of `clues` + `solutions`) | `check-solve` uniqueness verdict |

Every subsystem subscribes to the runtime event bus (`file:read`,
`clue:revealed`, `suspect:marked`, `dialogue:asked`, `scene:advanced`,
`accuse:attempt`, …) — author your own custom mechanic the same way.

See [`docs/developer-guide.md`](./docs/developer-guide.md) for the
full subsystem reference and a worked example.

## Current Limitations

What's still on the author:

- advanced puzzle balancing
- content generators for every evidence family (logs, registry rows,
  interviews) — the uniqueness solver tells you *if* your evidence is
  fair; it does not generate it for you
- non-English mystery localization
- time-pressure / inventory mechanics (template plugin shown in the
  developer guide; not first-class)

## Bottom Line

If you need one sentence:

`cli mystery starter pack` is a Python-based workspace for scaffolding, validating, and
local-playtesting filesystem-based command-line mystery games.
