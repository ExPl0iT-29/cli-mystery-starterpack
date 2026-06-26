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

The package lives in `cli_mystery_starter/` and exposes four core commands:

- `init <path>`: create a new mystery scaffold
- `validate <path>`: run scaffold and content-contract checks
- `play <path>`: run a mystery project in the reusable investigation shell
- `check-answer <path> <guess>`: verify a suspect name against a project

The generated project shape is centered around:

- `game/`: player-facing evidence and puzzle files
- `design/`: story truth and clue-graph planning
- `docs/`: project-specific author notes and schemas
- `hints/`: progressive player hints
- `tools/`: optional generators and validators

## Getting Started

Pick whichever fits how you want to work. All three end at the same `init` command.

### 1. Install from PyPI

```bash
pip install cli-mystery-starter
cli-mystery-starter init my-mystery
```

### 2. Use as a GitHub template

Click **Use this template** on the [repo](https://github.com/ExPl0iT-29/cli-mystery-starterpack),
create your own copy, then from `cli_mystery_starter/`:

```bash
python dev.py init ../my-mystery
```

### 3. Clone and run (no install)

```bash
git clone https://github.com/ExPl0iT-29/cli-mystery-starterpack
cd cli-mystery-starterpack/cli_mystery_starter
python dev.py init my-mystery
```

## Common Commands

Whether you installed the package (`cli-mystery-starter`) or run from source (`python dev.py`),
the subcommands are the same:

```bash
cli-mystery-starter validate my-mystery                 # check the project contract
cli-mystery-starter play my-mystery                     # playtest in the investigation shell
cli-mystery-starter init my-mystery --config examples/mystery_config.json   # custom metadata
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

## Current Limitations

The package currently gives you a strong starting structure, but it does not yet provide:

- deep schema validation
- automatic uniqueness checking for the final solution
- advanced puzzle balancing
- content generators for every evidence family

Those remain author responsibilities.

## Bottom Line

If you need one sentence:

`cli mystery starter pack` is a Python-based workspace for scaffolding, validating, and
local-playtesting filesystem-based command-line mystery games.
