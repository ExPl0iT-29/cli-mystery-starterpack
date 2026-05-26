# Codebase Structure

**Analysis Date:** 2026-04-29

## Directory Layout

```
cli mystery starter pack/
├── README.md                       # Top-level repo intro
├── cli_mystery_starter/            # Python package + tests + examples (the tool)
│   ├── README.md                   # Package usage docs
│   ├── pyproject.toml              # Build config, console script, py>=3.10, no deps
│   ├── dev.py                      # Developer runner (run without install)
│   ├── examples/
│   │   └── mystery_config.json     # Sample config for `init --config`
│   ├── src/
│   │   └── cli_mystery_starter/
│   │       ├── __init__.py         # Package marker
│   │       ├── __main__.py         # Enables `python -m cli_mystery_starter`
│   │       ├── cli.py              # argparse dispatch (init/validate/play/check-answer)
│   │       ├── scaffold.py         # Project generation, DEFAULT_CONFIG, load_config
│   │       ├── templates.py        # Pure text generators for every scaffolded file
│   │       ├── validation.py       # Static project linter (REQUIRED_PATHS etc.)
│   │       ├── runtime.py          # InvestigationShell (cmd.Cmd) + play_project
│   │       └── answer.py           # check_answer_command wrapper
│   └── tests/
│       └── test_cli_mystery_starter.py   # Tests for scaffold + validate + runtime
├── design_rules_cli/               # Design study + production blueprint (authoring guidance)
│   ├── README.md
│   ├── 00-repo-study-overview.md
│   ├── 01-game-design-study.md
│   ├── 02-engineering-study.md
│   ├── 03-writing-study.md
│   ├── 04-design-rules.md
│   ├── 05-production-blueprint.md
│   ├── 06-author-checklists.md
│   └── 07-bmad-study-checkpoints.md
└── docs/                           # Higher-level project documentation
    ├── index.md
    ├── project-overview.md
    ├── designing-cli-mystery-games.md
    ├── data-model.md
    └── bmad-checkpoints.md
```

## Directory Purposes

**`cli_mystery_starter/`:**
- Purpose: the installable Python tool that scaffolds, validates, and plays mystery projects.
- Contains: `pyproject.toml`, `dev.py`, `src/`, `tests/`, `examples/`.
- Key files: `pyproject.toml`, `src/cli_mystery_starter/cli.py`, `dev.py`.

**`cli_mystery_starter/src/cli_mystery_starter/`:**
- Purpose: the package's actual source modules (src-layout).
- Contains: one module per layer — CLI, scaffold, templates, validation, runtime, answer.
- Key files: `cli.py`, `runtime.py`, `scaffold.py`, `validation.py`, `templates.py`, `answer.py`.

**`cli_mystery_starter/src/cli_mystery_starter/`** module roles:
- `cli.py`: argparse parser and `main()` entry point (used by the `cli-mystery-starter` script).
- `__main__.py`: allows `python -m cli_mystery_starter`.
- `scaffold.py`: `create_project()`, `load_config()`, `DEFAULT_CONFIG`.
- `templates.py`: text body generators (no I/O).
- `validation.py`: `validate_project()` plus `REQUIRED_PATHS`, `EXPECTED_FOLDERS`, `EVIDENCE_FOLDERS` constants.
- `runtime.py`: `InvestigationShell`, `play_project`, `SURFACES` map, path sandboxing helpers, `check_answer`.
- `answer.py`: `check_answer_command` for the `check-answer` CLI and scaffolded `tools/check_answer.py`.

**`cli_mystery_starter/tests/`:**
- Purpose: pytest-style tests covering scaffold creation, validation pass/fail, and runtime helpers.
- Key files: `test_cli_mystery_starter.py`.

**`cli_mystery_starter/examples/`:**
- Purpose: sample inputs that authors can copy.
- Key files: `mystery_config.json`.

**`design_rules_cli/`:**
- Purpose: long-form study notes and authoring checklists distilled from analyzing existing CLI mystery games. Reference material, not code.
- Contains: numbered Markdown documents covering game design, engineering, writing, rules, production, checklists, and BMAD checkpoints.
- Key files: `04-design-rules.md`, `05-production-blueprint.md`, `06-author-checklists.md`.

**`docs/`:**
- Purpose: top-level human documentation for the starter pack as a whole.
- Contains: project overview, design guide, data model spec, BMAD checkpoints, doc index.
- Key files: `index.md`, `project-overview.md`, `data-model.md`, `designing-cli-mystery-games.md`.

## Key File Locations

**Entry Points:**
- `cli_mystery_starter/src/cli_mystery_starter/cli.py`: argparse dispatch and `main()`.
- `cli_mystery_starter/src/cli_mystery_starter/__main__.py`: `python -m` entry.
- `cli_mystery_starter/dev.py`: dev-mode runner.
- Console script `cli-mystery-starter` declared in `cli_mystery_starter/pyproject.toml`.

**Configuration:**
- `cli_mystery_starter/pyproject.toml`: build/packaging config.
- `cli_mystery_starter/examples/mystery_config.json`: sample per-project config.
- `cli_mystery_starter/src/cli_mystery_starter/scaffold.py`: `DEFAULT_CONFIG` constant.

**Core Logic:**
- `cli_mystery_starter/src/cli_mystery_starter/scaffold.py`: project creation.
- `cli_mystery_starter/src/cli_mystery_starter/templates.py`: file-body generation.
- `cli_mystery_starter/src/cli_mystery_starter/validation.py`: static validation rules.
- `cli_mystery_starter/src/cli_mystery_starter/runtime.py`: interactive shell.
- `cli_mystery_starter/src/cli_mystery_starter/answer.py`: answer verification command.

**Testing:**
- `cli_mystery_starter/tests/test_cli_mystery_starter.py`.

**Documentation:**
- `README.md` (repo root), `cli_mystery_starter/README.md`, `docs/`, `design_rules_cli/`.

## Naming Conventions

**Files:**
- Python modules: lowercase, single word (`cli.py`, `runtime.py`, `scaffold.py`).
- Scaffolded game files: lowercase nouns with no extension (`incident`, `people`, `instructions`, `solution`, `encoded`); hint files numbered (`hint1`–`hint4`).
- Markdown design docs: numbered prefix in `design_rules_cli/` (`04-design-rules.md`).

**Directories:**
- Authored game state lives under `game/` with plural family names (`interviews/`, `locations/`, `logs/`, `memberships/`, `registry/`).
- Authoring/meta lives under `design/`, `docs/`, `tools/`, `hints/`.
- Location stub files use `Title_Case_With_Underscores` (`East_Hall`, `North_Wing`, `South_Annex`).

## Where to Add New Code

**New CLI subcommand:**
- Implementation: register the subparser in `cli_mystery_starter/src/cli_mystery_starter/cli.py` `build_parser()` and add a branch in `main()`.
- Logic module: new file under `cli_mystery_starter/src/cli_mystery_starter/` (mirror `answer.py` size).

**New shell verb in the play runtime:**
- Add `do_<verb>` method to `InvestigationShell` in `cli_mystery_starter/src/cli_mystery_starter/runtime.py`.
- Update the help block in `do_help`.

**New runtime "surface" jump target:**
- Add an entry to `SURFACES` in `cli_mystery_starter/src/cli_mystery_starter/runtime.py` (line 10).

**New scaffolded file or folder for authors:**
- Add a generator function to `cli_mystery_starter/src/cli_mystery_starter/templates.py`.
- Wire it into the `files` dict (or `folders` list) in `scaffold.create_project()` in `scaffold.py`.
- Add a matching entry to `REQUIRED_PATHS` / `EXPECTED_FOLDERS` / `EVIDENCE_FOLDERS` in `validation.py` if it should be required.

**New validation rule:**
- Extend `validate_project()` in `cli_mystery_starter/src/cli_mystery_starter/validation.py`; append errors to the `errors` list.

**New tests:**
- Add to `cli_mystery_starter/tests/test_cli_mystery_starter.py` (single-file convention so far) or create a sibling `test_<area>.py` in the same `tests/` directory.

**New authoring guidance / design notes:**
- High-level: `docs/`.
- Detailed study or checklist: `design_rules_cli/` with the next numeric prefix.

**New authored mystery (not a code change):**
- Run `cli-mystery-starter init <somewhere>` outside this repo; do not commit generated mysteries into the starter pack.

## Special Directories

**`cli_mystery_starter/src/`:**
- Purpose: src-layout root so the package is only importable after install or via `dev.py`/editable install.
- Generated: No.
- Committed: Yes.

**`cli_mystery_starter/examples/`:**
- Purpose: sample author inputs.
- Generated: No.
- Committed: Yes.

**`design_rules_cli/` and `docs/`:**
- Purpose: reference documentation only; no executable code.
- Generated: No.
- Committed: Yes.

**Author-side `game/`, `hints/`, `design/`, `docs/`, `tools/` (inside a scaffolded project):**
- Purpose: produced by `cli-mystery-starter init` inside an *author's* project directory, not inside this repo.
- Generated: Yes (by `scaffold.create_project`).
- Committed: In the author's downstream repo, not here.

---

*Structure analysis: 2026-04-29*
