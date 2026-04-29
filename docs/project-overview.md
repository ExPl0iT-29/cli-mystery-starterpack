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

The package supports four core workflows:

1. `init`: scaffold a new mystery project from templates
2. `validate`: run scaffold and content-contract checks against an authored project
3. `play`: locally run a project in the reusable investigation shell
4. `check-answer`: verify a suspect name against the encoded solution

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

The package implementation is intentionally small:

- `cli.py`: argument parsing and command dispatch
- `runtime.py`: reusable investigation shell for authored projects
- `answer.py`: answer verification helper
- `scaffold.py`: config loading and file generation
- `templates.py`: text templates for generated files
- `validation.py`: project-contract checks for scaffolded projects

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

## Constraints And Non-Goals

This project does not currently provide:

- persistent runtime state
- save/load mechanics
- rich puzzle validation beyond the starter contract
- content-generation pipelines out of the box

Those are deliberate omissions. The starter pack is optimized for simple, portable,
text-first mystery projects.

## Recommended Reading Order For New Maintainers

1. Read [`cli_mystery_starter/README.md`](../cli_mystery_starter/README.md).
2. Review [`data-model.md`](./data-model.md) for scaffold and validation details.
3. Review [`designing-cli-mystery-games.md`](./designing-cli-mystery-games.md) for the authoring assumptions baked into the templates.

## Bottom Line

Describe this repository as:

`cli-mystery-starter` is a Python authoring tool that scaffolds, validates, and locally
playtests filesystem-based command-line mystery games.
