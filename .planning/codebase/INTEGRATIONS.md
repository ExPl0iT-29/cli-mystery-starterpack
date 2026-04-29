# External Integrations

**Analysis Date:** 2026-04-29

## APIs & External Services

**Third-party APIs:** None.

The starter pack is fully offline and self-contained. No HTTP clients, SDKs, or network calls are imported anywhere in `src/cli_mystery_starter/`. All operations are local filesystem reads/writes plus stdin/stdout I/O.

## Data Storage

**Databases:**
- None.

**File Storage:**
- Local filesystem only. Scaffolded mystery projects are directory trees written by `scaffold.create_project` (`src/cli_mystery_starter/scaffold.py`) using `pathlib.Path` and `templates.py` content blobs.
- Scaffold layout includes case files, suspect dossiers, evidence notes, and a `meta.json` consumed by `runtime.py` and `validation.py`.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. The "answer check" flow (`src/cli_mystery_starter/answer.py`, `runtime.check_answer`) compares an MD5 hash of the user's guess against a stored hash in the scaffolded project's metadata. This is a puzzle gate, not authentication.

## Monitoring & Observability

**Error Tracking:**
- None.

**Logs:**
- Plain `print()` to stdout in `cli.py` and `runtime.InvestigationShell`. No logging framework configured.

## CI/CD & Deployment

**Hosting:**
- Not applicable — distributed as source / Python package.

**CI Pipeline:**
- None detected. No `.github/`, `.gitlab-ci.yml`, or other CI config files at the project root.

## Environment Configuration

**Required env vars:**
- None.

**Secrets location:**
- None. No `.env` files, no credential stores, no secret references.

## Webhooks & Callbacks

**Incoming:** None.
**Outgoing:** None.

## CLI / Subprocess Integrations

- No `subprocess`, `os.system`, or external CLI invocations from the package.
- The starter itself **is** a CLI (`cli-mystery-starter` entry point in `pyproject.toml`) exposing four subcommands defined in `src/cli_mystery_starter/cli.py`:
  - `init <target> [--config <json>]` — scaffold a project
  - `validate <target>` — structural validation
  - `play <target>` — launch interactive `cmd.Cmd` shell
  - `check-answer <target> <guess>` — verify suspect guess
- Scaffolded child projects emit their own runnable Python entry (`templates.py` writes a script that imports `cli_mystery_starter.runtime.play_project` and `cli_mystery_starter.answer.check_answer_command`), creating a runtime dependency from generated projects back onto this package.

## Import Boundaries

**Internal package layers (within `src/cli_mystery_starter/`):**
- `cli.py` — top-level dispatcher; imports from `answer`, `runtime`, `scaffold`, `validation`
- `answer.py` — depends on `runtime` (`check_answer`, `load_title`, `validate_runtime_project`)
- `runtime.py` — leaf module; stdlib only (`cmd`, `hashlib`, `json`, `shlex`, `pathlib`)
- `scaffold.py` — depends on `templates`; stdlib `json`, `pathlib`
- `templates.py` — leaf for content; stdlib `hashlib.md5`, `pathlib`. Generated template strings reference `cli_mystery_starter.runtime` and `cli_mystery_starter.answer` as imports inside the scaffolded project (cross-package coupling at runtime of generated games).
- `validation.py` — leaf module; stdlib `json`, `re`, `pathlib`
- `__main__.py` — re-exports `cli.main` so `python -m cli_mystery_starter` works

**External boundaries:**
- Standard library only — no third-party imports anywhere in `src/` or `tests/`.
- `dev.py` (repo-level) and `tests/test_cli_mystery_starter.py` both manipulate `sys.path` to insert `cli_mystery_starter/src` before importing the package, enabling editable runs without install.

---

*Integration audit: 2026-04-29*
