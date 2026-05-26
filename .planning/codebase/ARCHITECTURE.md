# Architecture

**Analysis Date:** 2026-04-29

## Pattern Overview

**Overall:** Filesystem-as-game-database. A small Python package (`cli_mystery_starter`) provides a CLI that scaffolds, validates, and runs mystery games whose entire game state is encoded as a directory tree of plain-text files. There is no database, no network layer, and no runtime mutable state beyond in-memory shell session data (notes, suspects).

**Key Characteristics:**
- Authoring-first: the package's primary job is to generate a *project layout* that a human author edits.
- Content-as-code: gameplay content lives in files (`game/incident`, `game/people`, `game/locations/*`, etc.); the runtime simply reads them.
- Stateless runtime: `play` launches an interactive `cmd.Cmd` shell that traverses the project directory; only ephemeral session data exists.
- MD5-hash answer verification: the secret solution is stored as a hex digest in a file named `encoded`, never as plaintext.
- Stdlib-only Python (>=3.10), zero runtime dependencies (`pyproject.toml` line 14).

## Layers

**CLI / Entry layer:**
- Purpose: argparse dispatch for the four subcommands (`init`, `validate`, `play`, `check-answer`).
- Location: `cli_mystery_starter/src/cli_mystery_starter/cli.py`, `cli_mystery_starter/src/cli_mystery_starter/__main__.py`
- Contains: `build_parser()`, `main()`.
- Depends on: `scaffold`, `validation`, `runtime`, `answer`.
- Used by: console script `cli-mystery-starter` (declared in `pyproject.toml`) and `python -m cli_mystery_starter`.

**Scaffold layer:**
- Purpose: create a new mystery project on disk from a config dict.
- Location: `cli_mystery_starter/src/cli_mystery_starter/scaffold.py`
- Contains: `DEFAULT_CONFIG`, `load_config()`, `create_project()`, `ensure_clean_target()`, `write_text()`.
- Depends on: `templates` for file body generation.
- Used by: `cli.py` `init` command.

**Templates layer:**
- Purpose: pure functions returning the textual body of every scaffolded file (READMEs, incident stub, people stub, location stubs, hints, design docs, wrappers).
- Location: `cli_mystery_starter/src/cli_mystery_starter/templates.py`
- Contains: `slugify()`, `default_answer_hash()`, `root_readme()`, `instructions()`, `solution()`, `incident()`, `people()`, `location_stub()`, `hint()`, `story_bible()`, `clue_graph()`, `data_schemas()`, `family_stub()`, `play_wrapper()`, `answer_wrapper()`.
- Depends on: stdlib `hashlib` only.
- Used by: `scaffold.py`.

**Validation layer:**
- Purpose: static-check a generated/edited project against required paths, schema rules, and clue-marker counts.
- Location: `cli_mystery_starter/src/cli_mystery_starter/validation.py`
- Contains: `REQUIRED_PATHS`, `EXPECTED_FOLDERS`, `EVIDENCE_FOLDERS`, `validate_project()`.
- Depends on: stdlib only (`json`, `re`, `pathlib`).
- Used by: `cli.py` `validate` command.

**Runtime layer:**
- Purpose: interactive investigation shell. Reads files, sandboxes path traversal to project root, tracks notes/suspects, evaluates accusations.
- Location: `cli_mystery_starter/src/cli_mystery_starter/runtime.py`
- Contains: `SURFACES` map, `load_title()`, `resolve_project_path()`, `format_project_path()`, `check_answer()`, `validate_runtime_project()`, `InvestigationShell(cmd.Cmd)`, `play_project()`.
- Depends on: stdlib `cmd`, `hashlib`, `json`, `shlex`, `pathlib`.
- Used by: `cli.py` `play` command and the scaffolded `play.py` wrapper at the project root.

**Answer layer:**
- Purpose: thin command-line wrapper around `runtime.check_answer`.
- Location: `cli_mystery_starter/src/cli_mystery_starter/answer.py`
- Contains: `check_answer_command()`.
- Depends on: `runtime`.
- Used by: `cli.py` `check-answer` and the scaffolded `tools/check_answer.py` wrapper.

## Data Flow

**Scaffold flow (`init`):**
1. `cli.main()` parses args, loads config via `scaffold.load_config()` (merging optional JSON over `DEFAULT_CONFIG`).
2. `scaffold.create_project()` calls `ensure_clean_target()`, creates each folder in `config["folders"]`, and writes a fixed map of relative paths to template-generated text.
3. The placeholder answer "John Doe" is hashed with `templates.default_answer_hash()` and written to `encoded`.
4. `mystery_config.json` is serialized into the project root for later reference by `validate` and `runtime`.

**Validation flow (`validate`):**
1. `validation.validate_project()` checks each path in `REQUIRED_PATHS` exists.
2. Reads `mystery_config.json` if present; verifies `clue_marker` appears at least 3 times in `game/incident` and that all configured `folders` exist.
3. Verifies `game/people` has a header plus at least one record using `|` or tab delimiters.
4. Verifies `encoded` matches `^[0-9a-f]{32}$` (lowercase MD5).
5. Verifies wrapper scripts call the expected runtime/answer entry points.
6. Confirms each folder in `EVIDENCE_FOLDERS` contains at least one file.
7. Returns a list of errors; CLI exits 0 on empty list, 1 otherwise.

**Play flow (`play`):**
1. `runtime.play_project()` runs `validate_runtime_project()` (lighter than full `validate`: just checks `game`, `game/incident`, `game/people`, `hints`, `encoded`).
2. Constructs `InvestigationShell`, sets `current = project_root/game`, loads display title from `mystery_config.json`.
3. `cmd.Cmd.cmdloop()` reads commands; each `do_*` method resolves user paths through `resolve_project_path()` which raises `ValueError` if the path escapes the project root.
4. `do_accuse` hashes the guess and compares to `encoded` via `check_answer()`.

**State Management:**
- Persistent state: the project filesystem. No writes occur during `play`.
- Session state: `InvestigationShell.suspects: list[str]` and `case_notes: list[str]`, both lost on exit.

## Key Abstractions

**Project Root:**
- Purpose: a directory that satisfies `REQUIRED_PATHS` and contains the entire mystery.
- Examples: any directory produced by `init`; `cli_mystery_starter/examples/mystery_config.json` shows a config input.
- Pattern: every CLI subcommand takes a `target` path that is `resolve()`-d to an absolute project root.

**Surface (runtime shortcut):**
- Purpose: named jump-targets for the `open` command, mapping a keyword to a tuple of path parts under the project root.
- Examples: `runtime.py` line 10 `SURFACES` dict — `incident`, `people`, `logs`, `interviews`, `locations`, `registry`, `memberships`, `hints`, `design`.
- Pattern: extending the runtime with a new surface = adding one entry to this dict.

**Evidence Family:**
- Purpose: a top-level directory under `game/` containing one type of evidence (interviews, locations, memberships, logs, registry).
- Examples: `game/interviews/`, `game/locations/East_Hall`, etc.
- Pattern: each family has a stub README created by `templates.family_stub()`; validation requires at least one file per family.

**Encoded Answer:**
- Purpose: the final-answer secret stored as an MD5 hex digest in a file named `encoded`.
- Examples: `encoded` at the project root.
- Pattern: authors regenerate it via `templates.default_answer_hash()` or the bash one-liner shown in `templates.solution()`.

**Config (`mystery_config.json`):**
- Purpose: per-project authoring metadata (`project_name`, `display_title`, `theme`, `player_role`, `answer_type`, `clue_marker`, `folders`).
- Examples: `cli_mystery_starter/examples/mystery_config.json`, generated copy at any project root.
- Pattern: read by both `validation.validate_project()` and `runtime.load_title()`.

## Entry Points

**`cli-mystery-starter` console script:**
- Location: declared in `cli_mystery_starter/pyproject.toml` line 17, target `cli_mystery_starter.cli:main`.
- Triggers: user shell, or `python -m cli_mystery_starter` via `__main__.py`.
- Responsibilities: dispatch `init` / `validate` / `play` / `check-answer`.

**Scaffolded `play.py`:**
- Location: written by `templates.play_wrapper()` to `<project>/play.py`.
- Triggers: `python play.py` inside an authored project.
- Responsibilities: imports `cli_mystery_starter.runtime.play_project` and calls it on the script's directory.

**Scaffolded `tools/check_answer.py`:**
- Location: written by `templates.answer_wrapper()`.
- Triggers: `python tools/check_answer.py "<name>"`.
- Responsibilities: calls `cli_mystery_starter.answer.check_answer_command` against the project root (script's parent).

**Dev runner:**
- Location: `cli_mystery_starter/dev.py`.
- Purpose: developer-facing helper for running the package without installation.

## Error Handling

**Strategy:** Collect-and-return for batch validators, raise `ValueError` for path-sandbox violations inside the runtime, and rely on `argparse` for CLI usage errors.

**Patterns:**
- `validate_project()` and `validate_runtime_project()` return `list[str]` of human-readable errors; the CLI prints each prefixed with `- ` and exits with code 1.
- `resolve_project_path()` (`runtime.py` line 36) calls `Path.relative_to(root)` and raises `ValueError("Path escapes the case file.")` to prevent directory traversal out of the project.
- Shell `do_*` methods catch their own `ValueError`s and print friendly messages instead of crashing the loop.
- JSON config errors are reported as `Invalid JSON in mystery_config.json: <exc>`.

## Cross-Cutting Concerns

**Logging:** None. All user-visible output goes to `stdout` via `print()`.

**Validation:** Two-tier — full project validation (`validation.validate_project`) for `validate` command; minimal runtime preflight (`runtime.validate_runtime_project`) for `play` and `check-answer` commands.

**Authentication:** Not applicable. The only "secret" is the MD5 digest in `encoded`; correctness is verified by hashing the guess and comparing.

**Sandboxing:** The runtime resolves every user-provided path against `project_root` and refuses paths that fall outside it.

## Extension Points (Authoring New Mysteries)

Authors do not edit the `cli_mystery_starter` package. They produce a project and edit content files:

1. **Generate the scaffold:** `cli-mystery-starter init <target> [--config config.json]`. Optional config keys override `scaffold.DEFAULT_CONFIG` (project_name, display_title, theme, player_role, answer_type, clue_marker, folders).
2. **Edit story design first:** `design/story_bible.md` and `design/clue_graph.md` (templates from `templates.story_bible` / `templates.clue_graph`).
3. **Author the incident:** `game/incident` — must contain at least 3 occurrences of the configured `clue_marker` (default `CLUE`).
4. **Populate `game/people`:** tab- or pipe-delimited records with header.
5. **Author evidence families:** add real files under `game/interviews/`, `game/locations/`, `game/logs/`, `game/memberships/`, `game/registry/` (each must contain at least one file).
6. **Write hints:** `hints/hint1` … `hints/hint4` (the `do_hint` runtime command only accepts 1–4).
7. **Set the answer:** overwrite `encoded` with `md5(answer).hexdigest()` (one-liner shown in `solution`).
8. **Validate:** `cli-mystery-starter validate <project>` until errors are empty.
9. **Playtest:** `python play.py` or `cli-mystery-starter play <project>`.

**Extending the runtime itself:**
- Add a new surface jump: append to `SURFACES` in `runtime.py` line 10.
- Add a new shell verb: define a `do_<verb>` method on `InvestigationShell` and document it in `do_help`.
- Add a new validation rule: append to `validation.py`'s checks and update `REQUIRED_PATHS` / `EXPECTED_FOLDERS` if it implies new files.
- Add a new scaffolded file: add an entry to the `files` dict in `scaffold.create_project()` and a generator function in `templates.py`.

---

*Architecture analysis: 2026-04-29*
