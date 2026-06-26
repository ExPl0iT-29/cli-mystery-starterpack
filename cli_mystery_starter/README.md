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

Validation now checks:

- required scaffold files and folders
- presence of `play.py` and `tools/check_answer.py`
- valid `mystery_config.json`
- clue marker presence and minimum clue count in `game/incident`
- basic `game/people` structure
- `encoded` hash format
- wrapper integrity for runtime and answer-check helpers

Validation still does not prove puzzle quality or unique solvability.

## Tests

Run the automated test suite from this directory:

```bash
python -m unittest discover -s tests
```

## Publishing to PyPI

From this directory:

```bash
python -m pip install build twine
python -m build                       # writes dist/*.whl and dist/*.tar.gz
python -m twine upload dist/*          # needs a PyPI token in ~/.pypirc or TWINE_PASSWORD
```

Bump `version` in `pyproject.toml` before each release. Test the wheel locally first with
`pip install dist/cli_mystery_starter-<version>-py3-none-any.whl`.

## Why Python

Python is a good fit for this style of project because it is strong at:

- content generation
- schema validation
- packaging
- text processing
- cross-platform author tooling
