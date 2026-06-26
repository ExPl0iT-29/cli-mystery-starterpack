# Testing Patterns

**Analysis Date:** 2026-04-29

## Test Framework

**Runner:**
- Python stdlib `unittest` (no pytest, no nose)
- Test classes inherit from `unittest.TestCase`
- Config: none — there is no `pytest.ini`, no `[tool.pytest.ini_options]`, no `tox.ini`. Discovery is plain `unittest`.

**Assertion Library:**
- `unittest.TestCase` built-ins: `assertEqual`, `assertTrue`, `assertIn`
- `unittest.mock.patch` for monkey-patching

**Run Commands:**
```bash
# From repo root, against the package
python -m unittest discover -s cli_mystery_starter/tests -t cli_mystery_starter

# Or from the cli_mystery_starter/ subdirectory
cd cli_mystery_starter
python -m unittest discover

# Run the single test module directly
python cli_mystery_starter/tests/test_cli_mystery_starter.py
```

No coverage tool, watch mode, or test runner script is configured.

## Test File Organization

**Location:**
- Separate top-level `tests/` directory at `cli_mystery_starter/tests/` (not co-located with `src/`)
- Single test module currently: `tests/test_cli_mystery_starter.py`

**Naming:**
- Files: `test_<area>.py` (currently just `test_cli_mystery_starter.py`)
- Classes: PascalCase ending in `Tests`: `StarterPackTests`
- Methods: `test_<scenario>_<expected_outcome>` snake_case, e.g. `test_validate_fails_for_missing_hint_and_bad_hash`, `test_check_answer_command_accepts_default_answer`

**Structure:**
```
cli_mystery_starter/
├── src/
│   └── cli_mystery_starter/   # package under test
└── tests/
    └── test_cli_mystery_starter.py
```

## sys.path Bootstrap

Because the project uses a `src/` layout and is not installed during local development, the test module manually injects `src/` onto `sys.path` before importing the package:

```python
SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from cli_mystery_starter.cli import main
from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.scaffold import DEFAULT_CONFIG, create_project
from cli_mystery_starter.validation import validate_project
```

New test modules must replicate this bootstrap (or rely on `pip install -e .`).

## Test Structure

**Suite Organization:**
```python
class StarterPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def scaffold_case(self, name: str = "case") -> Path:
        target = self.root / name
        create_project(target, dict(DEFAULT_CONFIG))
        return target
```

**Patterns:**
- **Setup:** `tempfile.TemporaryDirectory()` per test in `setUp` — every test gets a fresh sandbox
- **Teardown:** `self.tmp.cleanup()` always runs to remove the temp tree
- **Helpers:** `scaffold_case()` is a per-class factory that scaffolds a default project; tests call it as a building block
- **Assertions:** prefer specific membership checks (`assertIn(expected_message, errors)`) over equality on whole lists, except where exact emptiness matters (`assertEqual(errors, [])`)

## Mocking

**Framework:** `unittest.mock.patch` (stdlib).

**Patterns:**
```python
with patch("cli_mystery_starter.cli.play_project", return_value=0) as mock_play:
    result = main(["play", str(target)])
self.assertEqual(result, 0)
mock_play.assert_called_once()
```

**What to Mock:**
- Long-running interactive entry points (the `cmd.Cmd` REPL loop) — patch `play_project` on the import site (`cli_mystery_starter.cli.play_project`), not the definition site
- External side effects that aren't the unit under test

**What NOT to Mock:**
- The filesystem — tests use real `tempfile.TemporaryDirectory` sandboxes and exercise real `Path` I/O via `create_project`, `validate_project`, and `InvestigationShell`
- Hashing, JSON, or other stdlib primitives — use real values

## Stdout Capture

The CLI prints user-facing output via `print()`. Tests capture it with `contextlib.redirect_stdout`:

```python
buffer = io.StringIO()
with redirect_stdout(buffer):
    result = main(["check-answer", str(target), "John Doe"])
self.assertIn("Correct: John Doe", buffer.getvalue())
```

This is also used to drive the interactive shell deterministically:

```python
shell = InvestigationShell(target)
buffer = io.StringIO()
with redirect_stdout(buffer):
    shell.onecmd("cat incident")
    shell.onecmd("accuse John Doe")
```

Note the use of `Cmd.onecmd(line)` to feed individual commands without entering `cmdloop()`.

## Fixtures and Factories

**Test Data:**
- No fixture files on disk
- `DEFAULT_CONFIG` from `cli_mystery_starter.scaffold` is the canonical fixture; tests `dict(DEFAULT_CONFIG)` to copy it before passing to `create_project`
- All scaffolded artifacts (incident, hints, encoded MD5, play.py, etc.) are produced by the real scaffolder — tests then mutate files (e.g., `(target / "encoded").write_text("not-a-hash\n", ...)`) to drive negative paths

**Location:**
- No `tests/fixtures/` directory — fixtures are produced in-process per test

## Coverage

**Requirements:** None enforced. No `coverage`, `pytest-cov`, or `.coveragerc` configured.

**View Coverage (manual):**
```bash
pip install coverage
coverage run -m unittest discover -s cli_mystery_starter/tests -t cli_mystery_starter
coverage report -m
```

## Test Types Currently Present

**Unit-ish tests:** `validate_project` and `validate_runtime_project` exercised against scaffold output (`test_validate_passes_on_fresh_scaffold`, `test_validate_fails_for_missing_hint_and_bad_hash`, `test_validate_fails_for_insufficient_clues`).

**CLI integration tests:** `main([...])` invoked end-to-end with real argv lists for `init`, `validate`, `check-answer`, and `play` (latter with the runtime mocked).

**Runtime/REPL integration:** `InvestigationShell` driven via `onecmd` to assert side effects (file printing, accusation acceptance).

**E2E:** Not used — there is no subprocess-based test of the installed `cli-mystery-starter` console script.

## Common Patterns

**End-to-end CLI invocation:**
```python
result = main(["init", str(target)])
self.assertEqual(result, 0)
self.assertTrue((target / "play.py").exists())
```

**Negative-path validation:**
```python
target = self.scaffold_case()
(target / "hints" / "hint4").unlink()
(target / "encoded").write_text("not-a-hash\n", encoding="utf-8")
errors = validate_project(target)
self.assertIn("Missing required path: hints/hint4", errors)
```

**Asserting a partial error message:** prefer `assertIn(substring, errors_list)` since validators return `list[str]` and the exact message wording is part of the contract.

**Module-as-script entry:** every test module ends with
```python
if __name__ == "__main__":
    unittest.main()
```
so a developer can run `python tests/test_cli_mystery_starter.py` directly.

## Adding New Tests

- Place new test files in `cli_mystery_starter/tests/` named `test_<area>.py`
- Re-use the `sys.path` bootstrap block at the top of the module
- Inherit from `unittest.TestCase`; use `tempfile.TemporaryDirectory` in `setUp`/`tearDown` for any test that touches the filesystem
- Build cases with the real scaffolder (`create_project(target, dict(DEFAULT_CONFIG))`) rather than hand-rolling fixture trees — this keeps tests aligned with the shipped scaffold
- Capture CLI output with `redirect_stdout(io.StringIO())` and assert on substrings
- Mock only long-running or genuinely external pieces (e.g., `cmdloop`); leave filesystem and hashing real

---

*Testing analysis: 2026-04-29*
