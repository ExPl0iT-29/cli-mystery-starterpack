# Ship-Ready Code Audit & Founder Review

## Executive Summary
`cli-mysterypack` is a small, dependency-free Python package that scaffolds, validates, playtests, and answer-checks filesystem-based CLI mystery games. It is an authoring toolchain, not a deployed web/mobile app — so most of the security and UX rubric (auth, CORS, XSS, retention loops, onboarding screens) is N/A. Since the previous audit the project gained real packaging: an MIT `LICENSE`, complete `pyproject.toml` metadata, three documented install paths (PyPI / GitHub template / clone), and a verified wheel+sdist build. 7/7 tests pass, the installed console command scaffolds a valid 25-file project, zero dependencies, no hardcoded secrets, no comment spam. It is ready to publish.

## Ship-Ready Score: **93 / 100**
- **Founder UX & Features:** 22 / 25
- **Security & Hardening:** 23 / 25
- **Code Cleanliness:** 25 / 25
- **AI Slop Level:** 23 / 25

**Status:** Launch Ready 🚀

(Scored against the package's real scope: a CLI authoring tool. Retention/analytics loops do not apply to an offline dev tool and are not penalized.)

---

## 1. Founder's Feature & UX Review

### Active Features
- `init <path>` — scaffolds a 25-file project (re-verified this run: writes 25 files, validates clean).
- `validate <path>` — checks required paths, clue-marker count, `people` delimiter, MD5 hash format, wrapper integrity.
- `play <path>` — interactive `cmd.Cmd` shell: `ls/cd/cat/head/tail/grep/open/note/mark/suspects/hint/accuse`.
- `check-answer <path> <guess>` — MD5 verification with a clean 0/1/2 exit-code contract.
- **New:** three onboarding paths now documented in the root README — `pip install`, "Use this template", and clone-and-run. This is the biggest UX win for "use as a template": a newcomer has a copy-paste command regardless of how they found the repo.

### Broken or Placeholder Features
None. Scaffold placeholder content (`John Doe` hash, `placeholder record N`, family stubs) is intentional template output, flagged with `Author note: replace ... before shipping`. No `TODO`/`FIXME` in `src/`.

### Product Growth Suggestions
1. **CI workflow (GitHub Actions)** — run tests on push + publish to PyPI on tag. The one remaining gap for a hands-off release; raises contributor trust on a template repo.
2. **Uniqueness heuristic in `validate`** — flag when a single `grep` reveals the culprit. Highest-value correctness check for the tool's actual purpose.
3. **`new-evidence` generator subcommand** — the most tedious authoring step (filling interview/log families) is currently fully manual.

---

## 2. Security Vulnerabilities

No critical, high, or medium findings. Offline CLI: no network, database, server, or HTML surface.

- **MD5 used for answer encoding** (Severity: Informational)
  - *Location:* `src/cli_mystery_starter/runtime.py:49-52`, `templates.py:10-11`
  - *Description:* Hashes the suspect name into `encoded`. Puzzle obfuscation, not credential protection — brute-forceable from the people list, which is fine for a game. Not a flaw; flagged so `encoded` is never mistaken for a secret store.
  - *Fix:* None required.

- **Path traversal in the investigation shell** (Severity: Resolved / N/A)
  - *Location:* `runtime.py:36-42` (`resolve_project_path`) — every path is `.resolve()`d and checked with `relative_to(root)`; `cd ../..` / `cat /etc/passwd` are blocked. Correctly handled.

- **Secrets scan:** clean. No keys/tokens/passwords. No `.env` needed (no secrets exist). `pip-audit` surface is empty — zero dependencies.

---

## 3. Dead Code & Bundle Bloat
- **Dead imports/variables removed:** None found. All 8 modules wired (`cli` → `answer`/`runtime`/`scaffold`/`validation`; `dev.py`/`__main__.py` are entry points).
- **Unused dependencies flagged:** None — `dependencies = []`.
- **Dead files/assets detected:** None in the tracked tree. `build/`/`dist/`/`*.egg-info/` are now gitignored. Note: the stale git worktree `.claude/worktrees/blissful-rhodes-bc9763/` still holds exploratory modules not part of the package — delete it if unused. The duplicate `cli_mystery_starter/LICENSE` is intentional (bundles into the wheel).

---

## 4. AI Slop & Code Polish
- **AI Comments Removed:** None needed — source carries no robotic comments.
- **Documentation Refactored:** READMEs lead with what the tool does, give copy-paste commands for all three install paths, and carry honest "Current Limitations". Package README gained a "Publishing to PyPI" section. Prior `/deslop` pass already removed hype ("elegant", "user journeys", etc.).

---

## 5. Next Steps for Launch
- **Confirm the PyPI name** `cli-mysterypack` is unowned on pypi.org; rename in `pyproject.toml` if taken.
- **Flip the GitHub template toggle** (repo Settings → "Template repository") so "Use this template" appears.
- **Optional:** add the GitHub Actions test/publish workflow (suggestion #1) for a tag-driven release.
- **Optional:** delete the stale `.claude/worktrees/` copy.
- No blocking issues. Safe to tag `0.1.0`, build, and `twine upload`.
