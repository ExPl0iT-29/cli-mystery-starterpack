# CLI Mystery Starter

A reusable Python starter repo for building command-line mystery games where the filesystem is the game board.

## What This Includes

- a Python package under `src/`
- a CLI command to scaffold a new mystery project
- lightweight content validation
- starter templates for:
  - `instructions`
  - hints
  - docs
  - game data folders
  - answer verification
- a sample design config file

## Recommended Use

Create new projects with:

```bash
python -m cli_mystery_starter init my-mystery
```

Or, from this folder:

```bash
python -m src.cli_mystery_starter init my-mystery
```

Then edit:

- `design/story_bible.md`
- `design/clue_graph.md`
- `game/incident`
- `game/people`
- `game/interviews/`
- `game/locations/`
- `hints/`

## Structure

```text
cli_mystery_starter/
├─ pyproject.toml
├─ src/
│  └─ cli_mystery_starter/
│     ├─ __init__.py
│     ├─ __main__.py
│     ├─ cli.py
│     ├─ scaffold.py
│     ├─ validation.py
│     └─ templates.py
├─ examples/
│  └─ mystery_config.json
└─ README.md
```

## Commands

- `init <path>`: create a new mystery project scaffold
- `validate <path>`: run lightweight checks against a scaffolded project

## Why Python

Python is a good fit for this style of project because it is strong at:

- content generation
- schema validation
- packaging
- text processing
- cross-platform author tooling
