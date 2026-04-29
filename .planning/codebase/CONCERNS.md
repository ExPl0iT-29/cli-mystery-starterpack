# Codebase Concerns

**Analysis Date:** 2026-04-29

## Tech Debt

**MD5 used as the answer-verification primitive:**
- Issue: `cli_mystery_starter/src/cli_mystery_starter/templates.py` (`default_answer_hash`) and `cli_mystery_starter/src/cli_mystery_starter/runtime.py` (`check_answer`) both rely on `hashlib.md5`. Validation in `validation.py` (lines 92-96) hard-codes a 32-char hex regex, so the format is locked to MD5.
- Files: `src/cli_mystery_starter/runtime.py`, `src/cli_mystery_starter/templates.py`, `src/cli_mystery_starter/validation.py`
- Impact: Trivially brute-forceable for short names. Players can read `encoded` and reverse-lookup the culprit with rainbow tables. Also blocks future moves to salted/hashed or HMAC-based answers without a coordinated change in three modules.
- Fix approach: Introduce an `answer_format` field in `mystery_config.json`, support salted SHA-256 (`{algo}${salt}${digest}` envelope), update `validate_project` regex to be format-aware, and provide a migration helper in `tools/`.

**Answer comparison is case- and whitespace-sensitive but undocumented:**
- Issue: `runtime.check_answer` calls `guess.strip()` then hashes. Any case difference, accented character, or punctuation variant fails silently. Authors are not told this in `templates.solution()` or `templates.instructions()`.
- Files: `src/cli_mystery_starter/runtime.py:49-52`, `src/cli_mystery_starter/templates.py:77-98`
- Impact: Frustrating false negatives during playtest; authors must guess the canonical form.
- Fix approach: Normalize (casefold + collapse whitespace) on both sides, or add an `accept` list of accepted forms. Document the chosen rule in the generated `solution` file.

**Default placeholder answer is the actual valid answer:**
- Issue: `scaffold.create_project` writes `templates.default_answer_hash("John Doe")` as the encoded answer. The first test (`test_check_answer_command_accepts_default_answer`) confirms this. There is no scaffolding-time prompt or validation flag warning the author to replace it.
- Files: `src/cli_mystery_starter/scaffold.py:65`, `src/cli_mystery_starter/templates.py:65-74`
- Impact: A scaffold that passes `validate` can still ship with `John Doe` as the canonical answer. `validate_project` does not flag the default hash as suspicious.
- Fix approach: Add a check in `validate_project` that warns if `encoded` matches `md5("John Doe")` and the project name still equals the default. Optionally have `init` accept `--answer` and refuse to write the placeholder unless `--placeholder-answer` is passed.

**`load_config` does no schema validation:**
- Issue: `scaffold.load_config` blindly merges user JSON over `DEFAULT_CONFIG`. A typo like `"folder"` instead of `"folders"` silently leaves the default. `clue_marker` could be any string (including empty or whitespace).
- Files: `src/cli_mystery_starter/scaffold.py:30-37`
- Impact: Unexpected scaffolds; later `validate_project` errors with no hint that the config was wrong.
- Fix approach: Whitelist known keys, type-check each, raise on unknown keys (or at least warn). Pull defaults and required keys into a single `CONFIG_SCHEMA` constant.

**Hint count hard-coded to four in three places:**
- Issue: `runtime.do_hint` rejects anything outside `{"1","2","3","4"}`. `validation.REQUIRED_PATHS` lists `hints/hint1..hint4`. `scaffold.create_project` writes exactly four hints. `templates.hint` only has bodies for 1-4.
- Files: `src/cli_mystery_starter/runtime.py:238-243`, `src/cli_mystery_starter/validation.py:8-24`, `src/cli_mystery_starter/scaffold.py:84-87`
- Impact: Authors who want 3 progressive hints, or 6, must edit code. The "4" magic number is duplicated.
- Fix approach: Read hint count from `mystery_config.json` (e.g., `"hint_count": 4`) and derive both the validator list and the runtime range from it.

**`InvestigationShell` reads every file in `grep` into memory:**
- Issue: `do_grep` calls `file_path.read_text()` per file. `_iter_files` recurses unbounded. Each scaffolded location stub is 100 lines, but author-provided logs/registries can be megabytes.
- Files: `src/cli_mystery_starter/runtime.py:171-193`, `runtime.py:99-102`
- Impact: Memory pressure and slow grep on large case files. No max-file-size guard. UTF-8 decode errors will crash the shell.
- Fix approach: Stream line-by-line, catch `UnicodeDecodeError`, optionally cap per-file size, and skip binary files.

**`do_head` / `do_tail` crash on non-integer count:**
- Issue: `int(parts[1])` raises `ValueError` on `head incident abc`. The shell does not catch it; cmd.Cmd will surface a traceback to the player.
- Files: `src/cli_mystery_starter/runtime.py:145-169`
- Impact: Player sees a Python traceback instead of a usage hint. Breaks immersion.
- Fix approach: Wrap the parse in try/except and print `Usage: head <path> [count]`.

**Hard-coded location/line cross-references in scaffold are misleading:**
- Issue: `templates.location_stub` writes 99 placeholder lines and overwrites lines 12, 44, 87 with "X lives here." `templates.people` then claims those line numbers. But `game/people` is a TSV; the address column is a free-text "East Hall, line 12" the validator never enforces.
- Files: `src/cli_mystery_starter/templates.py:119-132`
- Impact: Sample case feels coherent only by accident. Authors who edit `people` without editing the location files break the implicit puzzle. No test covers the cross-reference.
- Fix approach: Either document the contract in `docs/data_schemas.md` and add a validator that confirms each `people` address line number resolves in the matching location file, or remove the line-number pretense from the scaffold sample.

## Known Bugs

**`do_open <surface>` on a missing file raises uncaught `ValueError`:**
- Symptoms: `_read_file` raises when the surface points to a non-existent file (e.g., user deletes `game/incident`); `do_open` does not wrap the call.
- Files: `src/cli_mystery_starter/runtime.py:195-206`
- Trigger: `open incident` after deleting `game/incident`.
- Workaround: Run `validate` before `play`. Fix by wrapping in try/except.

**`do_open` lists directories that may map to a file (e.g., `incident`, `people`):**
- Symptoms: For surface keys whose target is a file (`incident`, `people`), `do_open` correctly prints. For directories it lists. But `_set_current` is only called for directories, so after `open incident` the prompt does not change. This is intentional for files but undocumented.
- Files: `src/cli_mystery_starter/runtime.py:195-206`
- Trigger: Mixed surface types confuse new authors.
- Workaround: Document or normalize behavior.

**Path-escape check uses `relative_to` but allows symlinks to escape:**
- Symptoms: `resolve_project_path` resolves and checks relative_to root, but if the project root contains a symlink that points outside, `Path.resolve()` follows it and the `relative_to` check passes only when the resolved path is still under the resolved root.
- Files: `src/cli_mystery_starter/runtime.py:36-42`
- Trigger: Author places a symlink in `game/`. May leak host filesystem in shared/CTF deployments.
- Workaround: Reject symlinks explicitly; or compare both `resolve()` and `parents` chain.

**`do_help <topic>` falls back to default `cmd.Cmd` help which lists `do_*` introspection-style:**
- Symptoms: Inconsistent help UX; the curated help only fires when no argument is passed.
- Files: `src/cli_mystery_starter/runtime.py:256-277`
- Trigger: `help cat` produces minimal/no output because there are no docstrings on `do_*` methods.
- Workaround: Add docstrings to each `do_*` method or override `do_help` for all topics.

## Security Considerations

**MD5 + no salt for the answer:**
- Risk: Trivial reversal of the canonical answer from `encoded` (see Tech Debt).
- Files: `src/cli_mystery_starter/runtime.py`, `src/cli_mystery_starter/templates.py`
- Current mitigation: None.
- Recommendations: Move to salted SHA-256 envelope; treat `encoded` as a commitment, not a secret.

**`scaffold.write_text` does not constrain target paths:**
- Risk: `create_project` honors the `folders` list from user-supplied JSON config. A malicious config with `"folders": ["../../etc"]` would create directories outside the target. `write_text` also follows symlinks if the target already exists with one.
- Files: `src/cli_mystery_starter/scaffold.py:46-55`
- Current mitigation: `ensure_clean_target` requires empty target, but `folders` are joined with `target /` without normalization.
- Recommendations: Reject folder strings that contain `..` or are absolute; resolve and check `relative_to(target)` before mkdir.

**`InvestigationShell` shell-out commands are not provided, but `cmd.Cmd` default precmd allows raw lines:**
- Risk: Authors might add `do_!` style escapes later. There is no security model documented.
- Files: `src/cli_mystery_starter/runtime.py`
- Current mitigation: No external `os.system` calls.
- Recommendations: Document in `docs/` that the shell is intentionally sandboxed to project root and only file-reading verbs are allowed.

## Performance Bottlenecks

**Repeated full-tree walks:**
- Problem: `do_grep` and `validate_project` (`rglob("*")` in `EVIDENCE_FOLDERS`) re-walk the filesystem every call. Fine for scaffolds, slow for large authored cases.
- Files: `src/cli_mystery_starter/runtime.py:99-102`, `src/cli_mystery_starter/validation.py:116-121`
- Cause: No caching, no early termination.
- Improvement path: For `validate`, short-circuit `has_file` with `next(path.iterdir(), None)` recursion; for `grep`, allow file-pattern filtering (`grep <pat> --in *.md`).

## Fragile Areas

**`templates.py` is a giant string blob with no testing of generated content:**
- Files: `src/cli_mystery_starter/templates.py`
- Why fragile: Any whitespace or marker change can break `validate_project` (e.g., changing `CLUE` count). Tests verify scaffold-then-validate roundtrip but not content shape.
- Safe modification: Run `python -m unittest tests.test_cli_mystery_starter` after every template edit; add snapshot tests on key files.
- Test coverage: Roundtrip yes; per-template unit tests no.

**Coupled validation contract across three modules:**
- Files: `src/cli_mystery_starter/scaffold.py`, `src/cli_mystery_starter/templates.py`, `src/cli_mystery_starter/validation.py`
- Why fragile: Adding a new required file requires touching all three (and the runtime if surface-related). Easy to forget one.
- Safe modification: Centralize the contract in a single `CONTRACT` data structure consumed by all three modules.
- Test coverage: One happy-path validate test; one negative test for hint4/encoded.

**`runtime.SURFACES` dict duplicates path knowledge from `validation.REQUIRED_PATHS`:**
- Files: `src/cli_mystery_starter/runtime.py:10-20`, `src/cli_mystery_starter/validation.py:8-24`
- Why fragile: Renaming a folder requires synchronizing both lists.
- Safe modification: Derive surfaces from the centralized contract.

## Scaling Limits

**Single test file with 7 tests:**
- Current capacity: `tests/test_cli_mystery_starter.py` covers init, validate (3 cases), check-answer, play dispatch, shell roundtrip.
- Limit: No coverage for: invalid configs, path traversal, symlink handling, large files, malformed `encoded`, `do_grep`/`do_head`/`do_tail`/`do_note`/`do_mark`, `load_title` JSON-decode error path.
- Scaling path: Split into per-module test files (`test_scaffold.py`, `test_validation.py`, `test_runtime.py`, `test_answer.py`) and add a fuzz-ish test that runs each shell command on a fresh scaffold.

**No CI configuration committed:**
- Current capacity: Manual `python -m unittest` invocation.
- Limit: Tests can silently rot.
- Scaling path: Add `.github/workflows/ci.yml` running `unittest` on Python 3.10/3.11/3.12.

## Dependencies at Risk

**`hashlib.md5` deprecation pressure:**
- Risk: FIPS-strict Python builds raise `ValueError: [digital envelope routines] unsupported` for MD5 unless `usedforsecurity=False` is passed. Current code passes nothing.
- Impact: `runtime.check_answer` and `templates.default_answer_hash` will crash on RHEL FIPS hosts.
- Migration plan: Pass `usedforsecurity=False` short-term; migrate to SHA-256 long-term.

**`cmd.Cmd` from stdlib:**
- Risk: Provides minimal UX; no rich output, no readline history persistence by default, no tab completion for project paths.
- Impact: Authors used to modern REPLs find it primitive.
- Migration plan: Optional opt-in to `prompt_toolkit` for completions; keep `cmd.Cmd` as fallback.

## Missing Critical Features

**No uniqueness check for the solution path:**
- Problem: `validate_project` cannot tell whether the clue graph actually narrows to a single suspect, or whether multiple suspects are equally consistent with the evidence. `docs/index.md` and `README.md` (Current Limitations) acknowledge this.
- Blocks: Author confidence, fair-play guarantees, contest-style mysteries.
- Recommended: A `tools/solver.py` that walks `design/clue_graph.md` references and confirms the solve chain terminates uniquely.

**No `init --force` or non-empty-target handling:**
- Problem: `ensure_clean_target` raises if any file exists. Authors iterating on scaffolds must `rm -rf` first.
- Blocks: Idempotent re-scaffolding, partial template upgrades.
- Recommended: `--force`, `--upgrade` (only adds missing files), or a dry-run.

**No content generators for evidence families:**
- Problem: README "Current Limitations" calls this out. Authors must hand-write 3-7 logs, interviews, registry rows for every case.
- Blocks: Authoring velocity.
- Recommended: Optional `tools/generate_logs.py`, `tools/generate_registry.py` with seeded randomness.

**No `mystery_config.json` schema documentation:**
- Problem: Only the example file documents the shape. No JSON Schema, no validator output describing accepted fields.
- Blocks: Tooling integrations, IDE autocomplete.
- Recommended: Ship a `schemas/mystery_config.schema.json` and reference it from `docs/data-model.md`.

**No `version` field in `mystery_config.json`:**
- Problem: Future contract changes have no migration signal.
- Blocks: Backward compatibility for older scaffolds.
- Recommended: Add `"contract_version": "1"` and have `validate_project` warn on mismatch.

**No `play` save/restore for notes and suspects:**
- Problem: `case_notes` and `suspects` live only in process memory; quitting the shell loses them.
- Blocks: Multi-session play, sharing case progress.
- Recommended: Persist to `.session.json` in project root (gitignored) on every mutation.

**No localization / theming hooks:**
- Problem: All strings are hard-coded English in `runtime.py` and `templates.py`.
- Blocks: Non-English mysteries; reskinning the verbs (`accuse` may not fit every theme).
- Recommended: Externalize prompt strings; allow `mystery_config.json` to override verbs.

## Test Coverage Gaps

**Path traversal / sandbox enforcement:**
- What's not tested: `resolve_project_path`'s rejection of `..` and absolute escapes.
- Files: `src/cli_mystery_starter/runtime.py:36-42`
- Risk: Regression could let `cat /etc/passwd` succeed.
- Priority: High.

**`load_config` with malformed or partial JSON:**
- What's not tested: Missing keys, wrong types (`folders` as dict), unknown keys.
- Files: `src/cli_mystery_starter/scaffold.py:30-37`
- Risk: Silent fallback to defaults; confusing scaffolds.
- Priority: High.

**`load_title` JSON-decode error fallback:**
- What's not tested: Corrupt `mystery_config.json` should still produce a humanized title.
- Files: `src/cli_mystery_starter/runtime.py:23-33`
- Risk: Untested except path; minor.
- Priority: Low.

**Shell verbs `head`, `tail`, `grep`, `note`, `notes`, `mark`, `suspects`, `hint`, `pwd`, `cd`, `ls`:**
- What's not tested: Only `cat` and `accuse` are exercised in `test_runtime_shell_can_read_and_accuse`.
- Files: `src/cli_mystery_starter/runtime.py:104-244`, `tests/test_cli_mystery_starter.py`
- Risk: Regressions in player-facing UX go unnoticed.
- Priority: High.

**`validate_project` for `mystery_config.json` field type errors:**
- What's not tested: `folders` not a list, `clue_marker` empty/whitespace.
- Files: `src/cli_mystery_starter/validation.py:54-79`
- Risk: Author misconfiguration not caught.
- Priority: Medium.

**`encoded` answer mismatch (negative path) of `check_answer_command`:**
- What's not tested: Only the correct answer is exercised.
- Files: `src/cli_mystery_starter/answer.py`
- Risk: Wrong-answer path could regress (return code, message).
- Priority: Medium.

**`init` with `--config` flag:**
- What's not tested: `examples/mystery_config.json` is never loaded by a test.
- Files: `examples/mystery_config.json`, `src/cli_mystery_starter/cli.py:42-48`
- Risk: Example drifts from accepted schema.
- Priority: Medium.

## Documentation / Code Mismatches

**README quick-start mixes "package directory" with project root:**
- Issue: Top-level `README.md` lines 60-81 show `cd cli_mystery_starter && python dev.py init my-mystery`. But `play.py` inside generated project does `from cli_mystery_starter.runtime import play_project`, which requires the package to be installed or on `PYTHONPATH`. A user who only ran `dev.py` without `pip install -e .` will get `ModuleNotFoundError` when running `python play.py` inside the generated case.
- Files: `README.md`, `cli_mystery_starter/dev.py`, generated `play.py` (from `templates.play_wrapper`)
- Fix approach: Either instruct `pip install -e cli_mystery_starter` in quick-start, or have `play_wrapper` perform the `sys.path` insert that `dev.py` does.

**Generated `README.md` instructs `python -m cli_mystery_starter validate .` but quick-start path does not install the package:**
- Files: `src/cli_mystery_starter/templates.py:14-60`
- Fix approach: Same as above; or have generated README link back to `dev.py`.

**`solution` template repeats the answer "John Doe":**
- Issue: `templates.solution()` literally tells the player the answer is `John Doe`. The file is shipped at the project root with no gitignore guidance.
- Files: `src/cli_mystery_starter/templates.py:77-98`
- Fix approach: Replace with placeholder `<your suspect>` and add a "delete or gitignore before sharing" warning.

**`README.md` (root) repeats validation command twice:**
- Issue: Generated root README has "Run validation with:" followed by the same command shown three lines earlier.
- Files: `src/cli_mystery_starter/templates.py:43-59`
- Fix approach: Remove the duplicate block.

**`mystery_config.json` `answer_type` field is unused:**
- Issue: Both `DEFAULT_CONFIG` and `examples/mystery_config.json` set `"answer_type": "culprit_name"`, but no code reads it.
- Files: `src/cli_mystery_starter/scaffold.py:9-27`, `src/cli_mystery_starter/validation.py`, `src/cli_mystery_starter/runtime.py`
- Fix approach: Either implement (multi-answer, code-word, location, etc.) or remove from the schema.

**`docs/` references vs `design_rules_cli/`:**
- Issue: Top-level README points to `docs/index.md` and `docs/project-overview.md` but the rich design study lives in `design_rules_cli/` and is not cross-linked from the package docs.
- Files: `README.md`, `docs/index.md`, `design_rules_cli/README.md`
- Fix approach: Add a "See also" section linking the design study from `docs/index.md`.

## Gameplay / Authoring Friction

**No `search` or `find` verb:**
- Problem: `grep` exists but only finds substrings within file contents; there is no command to search filenames. Authors of large cases need `find game/ -name '*ortega*'`.
- Recommended: Add `do_find` that walks the tree and matches names.

**`open <surface>` taxonomy is fixed:**
- Problem: Custom evidence families (e.g., `game/forensics`) are not reachable via `open`. Authors must teach players `cd game/forensics` instead.
- Files: `src/cli_mystery_starter/runtime.py:10-20`
- Recommended: Auto-derive surfaces from `mystery_config.json["folders"]`.

**No "review" or "summary" command:**
- Problem: Players cannot recap what they have read. `notes` only prints what they typed.
- Recommended: Track which files have been `cat`-ed and offer `progress`.

**Validation does not check hint quality:**
- Problem: `validate_project` checks hints exist, not that they are non-default. `templates.hint(1..4)` ships generic placeholders that pass validation forever.
- Files: `src/cli_mystery_starter/validation.py`, `src/cli_mystery_starter/templates.py:135-142`
- Recommended: Warn if any hint file equals the scaffold default verbatim.

**No `accuse --confirm` two-step:**
- Problem: A typo of `accuse John Doe` is final immediately. There is no soft-mode that says "are you sure?" in story-driven games.
- Files: `src/cli_mystery_starter/runtime.py:245-254`
- Recommended: Track attempts; require confirmation after first wrong guess; or limit attempts.

**Empty `quit`/`exit`/EOF asymmetry:**
- Problem: `Ctrl-D` (EOF) is not handled; `cmd.Cmd` default raises. Players may see a traceback when closing the terminal.
- Files: `src/cli_mystery_starter/runtime.py:279-285`
- Recommended: Add `do_EOF` that returns True.

## Dead / Unused Code

**`answer_type` config key:** see Documentation / Code Mismatches above.

**`templates.hint(number)` fallback for n>=5:** unreachable because `do_hint` rejects `n>4` and `scaffold.create_project` only writes hints 1-4. Either remove or wire to a configurable hint count.

**`InvestigationShell.case_notes` and `suspects` lists:** populated but never persisted, never read by any command other than the listing verbs themselves. Half-implemented feature.

---

*Concerns audit: 2026-04-29*
