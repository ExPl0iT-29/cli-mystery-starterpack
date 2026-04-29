# Coding Conventions

**Analysis Date:** 2026-04-29

## Naming Patterns

**Files:**
- snake_case Python modules: `cli.py`, `runtime.py`, `scaffold.py`, `templates.py`, `validation.py`, `answer.py`
- Test files prefixed with `test_`: `tests/test_cli_mystery_starter.py`
- Package directory uses snake_case: `cli_mystery_starter/`

**Functions:**
- snake_case throughout: `build_parser`, `load_config`, `create_project`, `validate_project`, `play_project`, `check_answer`, `resolve_project_path`, `format_project_path`
- Private/internal helpers prefixed with single underscore: `_prompt`, `_set_current`, `_read_file`, `_iter_files`
- `cmd.Cmd` shell handlers use the `do_<verb>` convention: `do_ls`, `do_cd`, `do_cat`, `do_grep`, `do_accuse`

**Variables:**
- snake_case for locals and parameters: `project_root`, `config_path`, `display_title`, `case_notes`
- Module-level constants in UPPER_SNAKE_CASE: `SURFACES`, `DEFAULT_CONFIG`, `REQUIRED_PATHS`, `EXPECTED_FOLDERS`, `EVIDENCE_FOLDERS`, `ROOT`, `SRC`

**Types/Classes:**
- PascalCase: `InvestigationShell`, `StarterPackTests`

## Code Style

**Formatting:**
- No formatter config detected (no `pyproject.toml [tool.black]`, no `ruff.toml`, no `.editorconfig`)
- 4-space indentation, ~100-col soft wrap observed
- Double-quoted strings used consistently
- Trailing commas in multi-line literals (e.g., `DEFAULT_CONFIG`, `REQUIRED_PATHS`)

**Linting:**
- No linter configured in `pyproject.toml`
- No `[tool.ruff]`, `[tool.flake8]`, `[tool.mypy]` sections present

**Python Version:**
- Target: `requires-python = ">=3.10"` (per `cli_mystery_starter/pyproject.toml`)
- Uses 3.10+ union syntax: `list[str] | None`, `Path | None`, `dict | None`

## Type Usage

**Always-on annotations:**
- Every module begins with `from __future__ import annotations` (defers evaluation, enables PEP 604 syntax broadly)
- Public functions are fully annotated: `def main(argv: list[str] | None = None) -> int:`
- Return types declared on every function, including `-> None`
- Local variable annotations used where type isn't obvious: `errors: list[str] = []`, `self.suspects: list[str] = []`

**Generic typing:**
- Built-in generics preferred over `typing.List`/`typing.Dict`: `list[str]`, `dict`, `list[Path]`
- `dict` annotations are often bare (e.g., `def load_config(...) -> dict:`) rather than `dict[str, Any]`

## Import Organization

**Order (observed in `runtime.py`, `cli.py`, `scaffold.py`):**
1. `from __future__ import annotations` (always first)
2. Stdlib imports, alphabetical: `argparse`, `cmd`, `hashlib`, `io`, `json`, `re`, `shlex`, `sys`, `tempfile`, `unittest`
3. `from pathlib import Path` (used throughout — pathlib is the standard for filesystem work)
4. Blank line, then intra-package relative imports: `from .answer import check_answer_command`, `from . import templates`

**Path Aliases:**
- None. Tests bootstrap `src/` onto `sys.path` manually:
  ```python
  SRC = Path(__file__).resolve().parents[1] / "src"
  sys.path.insert(0, str(SRC))
  ```
- `dev.py` uses the same pattern at the project root.

## Error Handling

**Patterns:**
- Errors surfaced as return values when batch-style: validators return `list[str]` of error messages (`validate_project`, `validate_runtime_project`); empty list = success
- Caller prints each error line-by-line with `- {error}` prefix and returns non-zero exit code
- Targeted `try/except` blocks catch specific exceptions: `json.JSONDecodeError`, `ValueError`
- Exception chaining used to preserve cause: `raise ValueError("Path escapes the case file.") from exc`
- `ValueError` is the workhorse for domain/user-input failures (path escape, missing file, is-a-directory)
- Inside `cmd.Cmd` handlers, exceptions are caught and printed (never propagated to the REPL loop)

## Logging

**Framework:** None. `print()` is used for all user-facing output (CLI is the UI).

**Patterns:**
- Status messages go to stdout: `print(f"Created scaffold at: {target}")`
- Validation failures printed as bulleted list before non-zero exit
- No `logging` module usage anywhere in `src/`

## Comments

**When to Comment:**
- Code is largely self-documenting; inline comments are rare
- No module-level docstrings in `src/cli_mystery_starter/*.py`
- No function docstrings on public APIs

**JSDoc/TSDoc-equivalent (docstrings):**
- Not used. Behavior is documented in `README.md` and `docs/` rather than docstrings.

## Function Design

**Size:** Small, single-purpose. Most functions ≤ 20 lines. The `cmd.Cmd` `do_*` handlers cap at ~15 lines.

**Parameters:**
- Positional `Path` objects for filesystem roots: `def play_project(project_root: Path) -> int:`
- Optional config inputs use `T | None` defaults: `def main(argv: list[str] | None = None) -> int:`
- `cmd.Cmd` handlers receive raw `arg: str` and parse internally with `shlex.split` or `.strip()`

**Return Values:**
- CLI commands return `int` exit codes (0 success, 1 validation failure, 2 unknown command)
- Validators return `list[str]` (errors) — empty means OK
- Predicates return `bool`: `check_answer(...) -> bool`
- Mutating shell handlers return `None`; quit-style handlers return `bool` to signal `cmd.Cmd` to exit

## Module Design

**Exports:**
- Package `__init__.py` declares only `__all__ = ["__version__"]` and `__version__ = "0.1.0"`
- Submodules are imported directly (`from cli_mystery_starter.cli import main`); no re-exports at the package root
- Console script entry point: `cli-mystery-starter = "cli_mystery_starter.cli:main"` (in `pyproject.toml`)
- Module execution supported via `python -m cli_mystery_starter` (`__main__.py` present)

**Barrel Files:**
- Not used. Each module is consumed directly by name.

## Project Layout Conventions

- `src/`-layout package per `[tool.setuptools] package-dir = {"" = "src"}`
- Single top-level package `cli_mystery_starter/` containing CLI, runtime shell, scaffolder, validator, templates, answer-check
- `dev.py` at the project root provides path-bootstrapped local entry without install
- No `requirements.txt`; `dependencies = []` in `pyproject.toml` — stdlib only

---

*Convention analysis: 2026-04-29*
