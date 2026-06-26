# Technology Stack

**Analysis Date:** 2026-04-29

## Languages

**Primary:**
- Python >=3.10 — entire `cli_mystery_starter` package (`src/cli_mystery_starter/*.py`), tests, and `dev.py` runner

**Secondary:**
- Markdown — design docs in `design_rules_cli/` and `docs/`, plus `README.md` files
- JSON — project metadata and scaffold config consumed by `scaffold.py` and `validation.py` (e.g., `examples/` configs)

## Runtime

**Environment:**
- CPython >=3.10 (uses PEP 604 `list[str] | None` annotations and `from __future__ import annotations` throughout)

**Package Manager:**
- pip (standard) — installs from `cli_mystery_starter/pyproject.toml`
- Lockfile: missing (no `requirements.txt`, `poetry.lock`, or `uv.lock`)

## Frameworks

**Core:**
- Python standard library only — no third-party runtime frameworks
  - `argparse` — CLI parsing in `src/cli_mystery_starter/cli.py`
  - `cmd.Cmd` — interactive investigation shell in `src/cli_mystery_starter/runtime.py`
  - `pathlib.Path` — filesystem traversal across all modules
  - `json` — config and metadata parsing in `scaffold.py`, `runtime.py`, `validation.py`
  - `hashlib` / `hashlib.md5` — answer hashing in `runtime.py` and `templates.py`
  - `shlex` — command tokenization inside the investigation shell
  - `re` — content validation in `validation.py`

**Testing:**
- `unittest` (stdlib) — `cli_mystery_starter/tests/test_cli_mystery_starter.py`
- `unittest.mock.patch` — input mocking for shell tests
- `tempfile.TemporaryDirectory` — isolated scaffold roots per test

**Build/Dev:**
- `setuptools>=68` — declared in `[build-system]` of `pyproject.toml`
- `dev.py` — local runner that prepends `src/` to `sys.path` and invokes `cli.main`

## Key Dependencies

**Critical:**
- None — `pyproject.toml` declares `dependencies = []` (zero third-party runtime deps)

**Infrastructure:**
- `setuptools` (build-time only) — packaging via `setuptools.build_meta`

## Configuration

**Environment:**
- No environment variables consumed
- Optional JSON config file passed via `cli-mystery-starter init --config <path>` and parsed by `scaffold.load_config` (`src/cli_mystery_starter/scaffold.py`)
- `DEFAULT_CONFIG` constant in `scaffold.py` provides fallback metadata

**Build:**
- `cli_mystery_starter/pyproject.toml` — declares package, entry point `cli-mystery-starter = "cli_mystery_starter.cli:main"`, src layout (`package-dir = {"" = "src"}`)

## Platform Requirements

**Development:**
- Python >=3.10 on any OS (Windows, macOS, Linux)
- No compiled extensions; pure Python
- Run locally via `python dev.py <command>` or after `pip install -e cli_mystery_starter/`

**Production:**
- Same as development — distributed as a Python package; no server or hosted target. The CLI is the deliverable.

---

*Stack analysis: 2026-04-29*
