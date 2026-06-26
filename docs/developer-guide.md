# CLI Mystery Starter Pack — Developer Guide

> A practical guide for authoring terminal-native mystery games with this
> starter pack. Pairs with the high-level overview in
> [`project-overview.md`](project-overview.md) and the design study in
> `../design_rules_cli/`.

---

## 1. Overview

**What this is.** A toolkit for building **single-case, terminal-native
mystery games** where the player investigates a sandboxed directory of
evidence files using a familiar Unix-flavored shell (`ls`, `cat`,
`grep`, `find`) and submits a final accusation.

**What you can build with it today:**
- Whodunit cases with one canonical culprit.
- CTF-style investigative puzzles where evidence is hidden across files.
- Onboarding exercises that teach Unix shell habits through narrative.

**What requires extending the engine** (see §6):
- Branching narratives, multi-act stories.
- Dialogue trees with NPCs.
- Time-pressure or resource mechanics.
- Multi-ending or partial-solve scoring.

---

## 2. Installation & Setup

```bash
git clone <this-repo>
cd cli_mystery_starter
pip install -e .            # exposes `cli-mystery-starter` on PATH
```

Verify:

```bash
cli-mystery-starter --help
python -m unittest discover -s tests -t .
```

**Requirements:** Python ≥ 3.10. Zero third-party dependencies.

For one-off use without install: `python dev.py <subcommand>`.

---

## 3. Project Structure (after `init`)

```
my-case/
├── .gitignore           # excludes .session.json and the author-only `solution`
├── README.md            # how to play
├── instructions         # in-game instructions
├── solution             # author-only — gitignored by default
├── encoded              # answer hash; format detected automatically
├── mystery_config.json  # project metadata (typed schema)
├── play.py              # convenience wrapper
├── design/
│   ├── story_bible.md   # author notes — characters, motive, timeline
│   └── clue_graph.md    # which clue points to which inference
├── docs/
│   └── data_schemas.md
├── game/
│   ├── incident         # inciting event, contains CLUE markers
│   ├── people           # tab/pipe-delimited registry of suspects
│   ├── interviews/      # one file per witness
│   ├── locations/       # one file per location surface
│   ├── logs/            # access/security/communication logs
│   ├── memberships/     # rosters, club lists, family ties
│   └── registry/        # ledgers, manifests, bookings
├── hints/
│   ├── hint1            # progressive hints
│   ├── hint2
│   ├── hint3
│   └── hint4
└── tools/
    └── check_answer.py
```

The on-disk shape is enforced by
[`contract.py`](../cli_mystery_starter/src/cli_mystery_starter/contract.py).
`scaffold`, `validation`, and `runtime` all derive their per-path
knowledge from a single `CONTRACT` tuple — adding a new evidence family
or required file is a one-line change there.

---

## 4. Core Concepts

### 4.1 Narrative is filesystem-shaped

There is no script and no scene tree. Players investigate by traversing
`game/`. The "story" is the sum of evidence + the inferences a player
draws. Authoring is **content-as-code**: you write Markdown and TSV;
the runtime just reads files.

### 4.2 Choices are minimal

The only consequential choice today is `accuse <name>`. Everything else
is information-gathering. Plan your case so the *path to the accusation*
is the gameplay.

### 4.3 State and persistence

Three layers of state:

| Layer | Where it lives | Lifetime |
|---|---|---|
| Project content | files in `game/`, `hints/`, `design/` | permanent (your repo) |
| Session state | `<project>/.session.json` | per-player, persists across runs |
| In-memory only | the `cmd.Cmd` shell loop | dies on exit |

Session state currently captures: notes (`note <text>`), suspects
(`mark <name>`), and visited files (auto-tracked on `cat`/`head`/`tail`/
`open`). It auto-saves on every mutation and on `quit`.

### 4.4 Validation is your CI

`cli-mystery-starter validate <project>` enforces:

- All required files and directories exist (driven by `CONTRACT`).
- Every evidence directory contains at least one file.
- `game/incident` contains the configured `clue_marker` at least 3 times.
- `game/people` has a header + at least one record with `|` or tab.
- `encoded` parses as a known answer format.
- `encoded` is *not* still the placeholder `John Doe` answer.
- Wrappers (`play.py`, `tools/check_answer.py`) call the right entry
  points.

Treat `validate` as a precondition for shipping — green means
*structurally playable*, not necessarily *good*.

### 4.5 Answer formats

Two formats supported by
[`verifier.py`](../cli_mystery_starter/src/cli_mystery_starter/verifier.py):

- **`sha256_salted`** (default for new scaffolds):
  `sha256$<salt-hex>$<digest-hex>`. Per-project random salt makes
  rainbow-table attacks impractical.
- **`md5_legacy`**: bare 32-char MD5 hex. Older scaffolds keep working.

Player guesses are `strip()`-ed and internal whitespace is collapsed to
a single space before hashing on `sha256_salted`. Case is preserved —
pick a canonical spelling and document it for the player.

Set the answer programmatically:

```bash
python -c "from cli_mystery_starter.verifier import hash_answer; print(hash_answer('Maria Ortega'))" > encoded
```

---

## 5. Creating a New Game

### Step 1 — Scaffold

```bash
cli-mystery-starter init my-case --config my-config.json
```

A minimal `my-config.json`:

```json
{
  "project_name": "ortega-case",
  "display_title": "The Ortega Inheritance",
  "theme": "Edwardian estate",
  "player_role": "private investigator",
  "clue_marker": "[clue]",
  "answer_format": "sha256_salted",
  "hint_count": 4,
  "folders": [
    "game/interviews", "game/locations", "game/memberships",
    "game/logs", "game/registry",
    "hints", "docs", "design", "tools"
  ]
}
```

Unknown keys are rejected; folder paths cannot contain `..` or be
absolute (see
[`config.py`](../cli_mystery_starter/src/cli_mystery_starter/config.py)).

### Step 2 — Design first

Edit `design/story_bible.md` — characters, timeline, motive, **the
canonical answer**. Then `design/clue_graph.md` — which evidence file
points to which suspect. Aim for *exactly one chain* that narrows to
one person.

### Step 3 — Author the incident

Open `game/incident`. Write the inciting event in prose. Embed at least
3 occurrences of your `clue_marker`. These are the *anchor* clues the
validator looks for.

### Step 4 — Populate `game/people`

Header row + one record per suspect. Tab- or pipe-delimited. Suggested
columns: `NAME | ROLE | LOCATION | ALIBI`.

### Step 5 — Author evidence families

Each subfolder under `game/` needs at least one real file. Suggested
counts: 3–7 interviews, 4–8 location surfaces (with most being
misdirection), 2–5 logs/registries.

**Plant your real solve chain across 3–4 files**, separated by
inference steps. Misdirection should be coherent, not random — readers
can tell the difference.

### Step 6 — Write hints

`hints/hint1` to `hints/hint4` (count is configurable via
`hint_count`). Hints should be progressive: hint1 = "look at the
security log"; hint4 = "X was at Y at time Z". Players use them as a
ladder, not a spoiler dump.

### Step 7 — Set the answer

```bash
python -c "from cli_mystery_starter.verifier import hash_answer; \
           print(hash_answer('Maria Ortega'))" > my-case/encoded
```

Confirm: `python tools/check_answer.py "Maria Ortega"` prints success.

### Step 8 — Validate

```bash
cli-mystery-starter validate my-case
```

Iterate until empty.

### Step 9 — Playtest

```bash
python my-case/play.py
```

Solve it without your notes. If the solve chain isn't reachable from
`cat incident` alone, add a pointer.

### Step 10 — Ship

`solution` and `.session.json` are already in `.gitignore` from the
scaffold. Commit. Distribute as a tarball or repo.

---

## 6. Extending the Engine

### Add a shell verb

1. In
   [`runtime.py`](../cli_mystery_starter/src/cli_mystery_starter/runtime.py),
   define `def do_<verb>(self, arg: str) -> None:` with a one-line
   docstring (used by `help <verb>`).
2. Add a corresponding line in `do_help`'s curated block so it appears
   in the unfiltered help.
3. Add a test in `tests/test_runtime.py`.

### Add a required file or evidence family

Single source of truth lives in
[`contract.py`](../cli_mystery_starter/src/cli_mystery_starter/contract.py).
Append a `Surface(...)` row:

```python
Surface("forensics", ("game", "forensics"), "dir", is_evidence=True),
```

Then add the corresponding template body in `templates.py` and a row in
`scaffold.py`'s `files` dict so new scaffolds populate it.
`validation` and `runtime.SURFACES` pick up the change automatically.

### Add a new answer format

1. In
   [`verifier.py`](../cli_mystery_starter/src/cli_mystery_starter/verifier.py),
   define a recogniser regex and add cases to `hash_answer` /
   `verify` / `detect_format`.
2. Add the format name to `KNOWN_FORMATS`.
3. Add tests in `tests/test_verifier_and_config.py`.
4. Bump `config.CONTRACT_VERSION` if this changes the on-disk contract.

### Custom systems via the event bus

The runtime emits a small set of well-known events as the player
acts:

| Event | Payload | Emitted by |
|---|---|---|
| `file:read`       | `{path}`                                   | every `cat` / `head` / `tail` / `open` of a file |
| `clue:revealed`   | `{id, via}`                                | `ClueRegistry` on first discovery |
| `suspect:marked`  | `{name}`                                   | `do_mark` |
| `note:added`      | `{text, index}`                            | `do_note` |
| `hint:read`       | `{number}`                                 | `do_hint` |
| `dialogue:asked`  | `{npc, topic}`                             | `do_ask` (a topic with a known response) |
| `scene:advanced`  | `{from, to, narration}`                    | `SceneRouter` on transition |
| `accuse:attempt`  | `{guess, correct, fields_correct, ending}` | `do_accuse` |

Every optional subsystem the framework ships (clues, dialogue,
scenes) is just a subscriber. Author your own:

```python
class TimePressure:
    def __init__(self, budget_minutes=120):
        self.remaining = budget_minutes

    def attach(self, bus):
        bus.subscribe("file:read",      lambda _: self._spend(5))
        bus.subscribe("dialogue:asked", lambda _: self._spend(30))
        bus.subscribe("hint:read",      lambda _: self._spend(15))

    def _spend(self, minutes):
        self.remaining = max(0, self.remaining - minutes)
```

Wire it via a custom `InvestigationShell` subclass that overrides
`_wire_default_subscribers`, or — for distribution — drop a
discovery loop into the shell `__init__` that imports
`mystery/plugins/*.py`.

---

## 6.5 Optional Subsystems (data-driven, no code edits)

Each subsystem is **opt-in**: drop the JSON file in, and the
runtime picks it up. A scaffolded case without any of these files
behaves exactly as it did on day one.

### 6.5.1 Clue object model — `game/clues.json`

```json
[
  {
    "id": "ledger_44",
    "title": "Mismatched signature in the East Hall ledger",
    "source_path": "game/registry/ledger.txt",
    "tags": ["timeline", "alibi:butler", "points:maria_ortega"]
  }
]
```

When the player `cat`s `source_path`, the clue is auto-marked
discovered (and emits `clue:revealed`). The `clues` verb shows
collected clues; the journal recap shows the discovered count.
Discovered ids persist across sessions in `.session.json`.

Use `points:<slug>` and `exonerates:<slug>` tags to participate in
the uniqueness solver (§6.5.5).

### 6.5.2 Multi-field, multi-ending — `solutions.json`

```json
{
  "answers": {
    "culprit": {"value": "Maria Ortega", "aliases": ["Ortega"]},
    "motive":  {"value": "inheritance"},
    "weapon":  {"value": "chandelier"}
  },
  "endings": [
    {"id": "full_solve",
     "requires": ["culprit", "motive", "weapon"],
     "text": "You proved every piece of the case."},
    {"id": "partial",
     "requires": ["culprit"],
     "text": "Right person — wrong story."}
  ]
}
```

Player UX:

```
accuse Maria Ortega                                # legacy: culprit only
accuse culprit="Maria Ortega" motive=inheritance   # multi-field
```

Field matching is case-insensitive and whitespace-collapsing;
aliases let you accept multiple spellings. Endings fire in declared
order; the first whose `requires` are all matched wins. When
`solutions.json` is absent, the runtime falls back to the legacy
`encoded` flow.

### 6.5.3 NPC dialogue — `game/dialogue/<slug>.json`

```json
{
  "name": "The Butler",
  "greeting": "I served the family for thirty years.",
  "topics": [
    {
      "id": "chandelier",
      "summary": "the chandelier",
      "response": "I oiled it last Tuesday.",
      "reveals_clue": "butler_alibi_break"
    },
    {
      "id": "midnight",
      "summary": "the midnight gap",
      "requires_clues": ["butler_alibi_break"],
      "response": "Fine. I was in the cellar."
    }
  ]
}
```

Player UX:

```
ask butler                       # greet + list available topics
ask butler about chandelier      # response, may reveal a clue
```

Topics declare `requires_clues`; until those are discovered the NPC
deflects. `reveals_clue` chains progression: asking unlocks new
clues that unlock new topics that unlock later scenes.

### 6.5.4 Scene/beat engine — `game/scenes.json`

```json
{
  "start": "discover",
  "scenes": [
    {"id": "discover",
     "narration": "The chandelier still swings.",
     "advances_to": "confront",
     "advance_when": {"files_read": ["game/incident"]}},
    {"id": "confront",
     "narration": "You corner the butler in the East Hall.",
     "advances_to": "verdict",
     "advance_when": {"clues": ["butler_alibi_break"]}},
    {"id": "verdict",
     "narration": "Time for the accusation.",
     "advances_to": null}
  ]
}
```

Predicates available in `advance_when`:

- `files_read`      — every path must appear in the player's visited set
- `clues`           — every clue id must be discovered
- `suspects_marked` — every name must have been `mark`-ed
- `topics_asked`    — list of `"<npc>:<topic>"` pairs

The `scene` verb shows the current beat with a met/unmet checklist.
Scenes with `advances_to: null` are final. Current scene persists
across runs.

### 6.5.5 Uniqueness solver — `cli-mystery-starter check-solve`

Combines `game/clues.json` + `solutions.json` to verify the case
narrows to exactly one suspect. Tag clues with `points:<slug>` and
`exonerates:<slug>` (slug = lowercase, spaces → underscores). Then:

```bash
cli-mystery-starter check-solve my-case
```

| Verdict | Meaning | Exit |
|---|---|---|
| `UNIQUE`       | One strict top scorer, matches canonical culprit | 0 |
| `AMBIGUOUS`    | Two or more suspects tie at the top              | 1 |
| `MISMATCH`     | Top scorer is not the canonical culprit          | 1 |
| `INSUFFICIENT` | Not enough information to analyze                | 0 |
| `ERROR`        | Structural problems block analysis               | 1 |

Run it before shipping. Heuristic, not a full constraint solver,
but it catches the common "my evidence doesn't actually prove the
case" failure mode.

---

## 7. Best Practices

### Authoring

- **Design the solve chain on paper before writing any prose.** Every
  clue should be a step in exactly one logical chain.
- **Plant 1.5× the clues you need.** Redundancy beats brittleness;
  players miss things.
- **Misdirection is a coherent micro-narrative**, not random noise.
- **Test your hints in escalating order.** If hint1 alone cracks the
  case, it's too strong.
- **Keep file sizes under ~100 lines.** Reading 300 lines in `cat` is
  hostile. Many short files cross-referenced beats one long file.
- **Use `grep`-friendly text.** Suspect names should be uniquely
  searchable (`"Ortega"` good; `"John"` bad).
- **Never publish `solution` or readable plaintext answers.** The
  default `.gitignore` protects this; keep it.

### Engineering

- **Read [`contract.py`](../cli_mystery_starter/src/cli_mystery_starter/contract.py) first.** It is the spec.
- **Run tests after every template edit.**
  `python -m unittest discover -s tests -t .` from `cli_mystery_starter/`.
- **Re-run `validate` after every save** during authoring — fast and
  cheap.
- **Commit `mystery_config.json`** so reviewers can reproduce.
- **Don't edit the package to add a single hint** — change `hint_count`
  in your config (when wired through) or accept the M3 schema's defaults.

### Player UX

- Lead with a single starting prompt: `cat incident`. Don't make the
  first action ambiguous.
- The `progress` and `journal` verbs help long sessions feel less
  amnesiac. Mention them in `instructions`.
- Case sensitivity on `accuse` is intentional but bites; tell the
  player which spelling counts.

---

## 8. CLI Reference

| Subcommand | Purpose |
|---|---|
| `cli-mystery-starter init <target> [--config c.json]` | scaffold a new project |
| `cli-mystery-starter validate <project>` | check the project against `contract.py` |
| `cli-mystery-starter play <project>` | open the interactive shell |
| `cli-mystery-starter check-answer <project> <guess>` | non-interactive answer verify |
| `cli-mystery-starter check-solve <project>` | heuristic uniqueness verdict on the clue graph |

### Shell verbs (inside `play`)

| Verb | What it does |
|---|---|
| `ls [path]` | list directory contents |
| `cd <path>` | change directory (defaults to `game/`) |
| `pwd` | current location relative to project root |
| `cat <path>` | print a file (records visit) |
| `head <path> [n]` / `tail <path> [n]` | first/last lines |
| `grep <text> [path]` | substring search across file contents |
| `find <text> [path]` | substring search across filenames |
| `open <surface>` | jump to a known surface (incident, people, logs, …) |
| `progress` | how many `game/` files you have read |
| `journal` | recap of files read, suspects, and notes |
| `note <text>` / `notes` | record / list notes |
| `mark <name>` / `suspects` | record / list suspects |
| `hint <1-4>` | read a progressive hint |
| `clues` | list discovered clues (when `game/clues.json` exists) |
| `ask <npc> [about <topic>]` | probe an NPC (when `game/dialogue/` exists) |
| `scene` | show the current scene + advancement criteria (when `game/scenes.json` exists) |
| `accuse <name>` / `accuse culprit=… motive=… weapon=…` | submit your final answer |
| `save` | write progress to `.session.json` |
| `quit` (or `Ctrl-D`) | save and exit |

---

## 9. Where things live

| Concern | File |
|---|---|
| Project shape (single source of truth) | [`contract.py`](../cli_mystery_starter/src/cli_mystery_starter/contract.py) |
| CLI dispatch | [`cli.py`](../cli_mystery_starter/src/cli_mystery_starter/cli.py) |
| Scaffolding | [`scaffold.py`](../cli_mystery_starter/src/cli_mystery_starter/scaffold.py) |
| File-body templates | [`templates.py`](../cli_mystery_starter/src/cli_mystery_starter/templates.py) |
| Validation rules | [`validation.py`](../cli_mystery_starter/src/cli_mystery_starter/validation.py) |
| Investigation shell | [`runtime.py`](../cli_mystery_starter/src/cli_mystery_starter/runtime.py) |
| Answer hash formats | [`verifier.py`](../cli_mystery_starter/src/cli_mystery_starter/verifier.py) |
| Typed config schema | [`config.py`](../cli_mystery_starter/src/cli_mystery_starter/config.py) |
| Per-player session state | [`session.py`](../cli_mystery_starter/src/cli_mystery_starter/session.py) |
| Event bus (subscribe/emit) | [`events.py`](../cli_mystery_starter/src/cli_mystery_starter/events.py) |
| Clue object model | [`clues.py`](../cli_mystery_starter/src/cli_mystery_starter/clues.py) |
| Multi-ending solutions | [`solutions.py`](../cli_mystery_starter/src/cli_mystery_starter/solutions.py) |
| NPC dialogue system | [`dialogue.py`](../cli_mystery_starter/src/cli_mystery_starter/dialogue.py) |
| Scene/beat engine | [`scenes.py`](../cli_mystery_starter/src/cli_mystery_starter/scenes.py) |
| Uniqueness solver | [`solver.py`](../cli_mystery_starter/src/cli_mystery_starter/solver.py) |

For broader design context: see [`../design_rules_cli/README.md`](../design_rules_cli/README.md).
