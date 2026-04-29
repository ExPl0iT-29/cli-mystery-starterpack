from __future__ import annotations

from hashlib import md5


def slugify(value: str) -> str:
    return "-".join(part for part in value.strip().lower().replace("_", " ").split() if part)


def default_answer_hash(answer: str) -> str:
    return md5(answer.encode("utf-8"), usedforsecurity=False).hexdigest()


def root_readme(project_name: str, display_title: str) -> str:
    return f"""# {display_title}

`{project_name}` is a filesystem-based CLI mystery game scaffolded from `cli_mystery_starter`.

## Start Here

1. Run `python play.py`
2. Use `cat incident` or `open incident`
3. Follow the evidence through `people`, `locations`, `interviews`, `logs`, and `registry`
4. Finish with `accuse <name>`

## Authoring

Edit these first:

- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`
- `game/incident`

## Development Commands

Interactive playtest:

```bash
python play.py
```

Project validation:

```bash
python -m cli_mystery_starter validate .
```

Answer verification:

```bash
python tools/check_answer.py "<your suspect>"
```
"""


def instructions(display_title: str) -> str:
    return f"""Welcome to {display_title}.

Start by running `python play.py` and reading the `incident` file.

Important notes:

- the real clues are marked with `CLUE`
- if you get stuck, read the files in `hints/`
- to check your answer, use `accuse <name>` or `python tools/check_answer.py "<name>"`
- do not start by opening every file manually; search and cross-reference them
"""


def solution() -> str:
    return """Checking Your Answer
====================

NOTE TO AUTHORS:
- This file is for *you*, not the player. Add it to .gitignore or delete it
  before shipping. Anyone who reads it learns the canonical answer.

In the interactive runtime:

    accuse "<your suspect>"

Through the helper script:

    python tools/check_answer.py "<your suspect>"

Regenerate the encoded hash whenever you change the canonical answer:

    python -c "import hashlib; print(hashlib.md5(b'YOUR ANSWER', usedforsecurity=False).hexdigest())" > encoded

Comparison rules:
- the player's guess is `.strip()`-ed before hashing
- comparison is exact (case- and punctuation-sensitive); pick a canonical
  spelling and document it for the player

Author checklist:
- replace the placeholder `John Doe` hash with your real answer's hash
- delete or .gitignore this `solution` file before sharing the case
"""


def incident(clue_marker: str) -> str:
    return f"""***************
Incident Report
***************

This is the opening investigation file.

Use this file to establish:
- the incident
- the stakes
- the first useful leads

{clue_marker}: Add the first clear pivot clue here.
{clue_marker}: Add a second clue that points toward a different data family.
{clue_marker}: Add a suspect trait, object, organization, or location signal.
"""


def people() -> str:
    return """NAME\tROLE\tAGE\tADDRESS
Alex Mercer\tArchivist\t41\tEast Hall, line 12
Mina Ortega\tCurator\t35\tNorth Wing, line 44
Leena Voss\tAssistant Curator\t29\tSouth Annex, line 87
"""


def location_stub(name: str) -> str:
    lines = [f"placeholder record {i}" for i in range(1, 100)]
    lines[11] = "Alex Mercer lives here."
    lines[43] = "Mina Ortega lives here."
    lines[86] = "Leena Voss lives here."
    return "\n".join(lines) + "\n"


def hint(number: int) -> str:
    hints = {
        1: "Look at the structure of `game/incident` and search for the clue marker first.",
        2: "Use `head`, `grep`, and `cat` before manually browsing deeper folders.",
        3: "The people file tells you who exists and where to look next.",
        4: "If an address points to a line number, extract only that line from the location file.",
    }
    return hints.get(number, f"Add hint {number} here.\n")


def story_bible(display_title: str, theme: str, player_role: str) -> str:
    return f"""# Story Bible

## Project

- Title: {display_title}
- Theme: {theme}
- Player Role: {player_role}

## Hidden Truth

Write:

- what actually happened
- who did it
- why they did it
- what false leads exist
- what evidence confirms the answer
"""


def clue_graph() -> str:
    return """# Clue Graph

Define the solve path:

1. Starting clue in `game/incident`
2. First pivot into `game/people`
3. Second pivot into `game/locations/`, `game/interviews/`, or `game/logs/`
4. Narrowing step through another evidence family
5. Final confirmation

Make sure no single search reveals the answer immediately.
"""


def data_schemas() -> str:
    return """# Data Schemas

## incident

- narrative dump
- real clues marked with `CLUE`

## people

- tab-separated or pipe-separated records
- should map names to next-step lookups

## locations

- one file per street/room/zone
- line-based or block-based lookup

## interviews / logs / memberships / registry

- keep each family internally consistent
"""


def family_stub(title: str, purpose: str) -> str:
    return f"""# {title}

Purpose:
- {purpose}

Author note:
- replace this stub with real case content before shipping
"""


def play_wrapper() -> str:
    return """from __future__ import annotations

from pathlib import Path

from cli_mystery_starter.runtime import play_project


if __name__ == "__main__":
    raise SystemExit(play_project(Path(__file__).resolve().parent))
"""


def answer_wrapper() -> str:
    return """from __future__ import annotations

import sys
from pathlib import Path

from cli_mystery_starter.answer import check_answer_command


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python tools/check_answer.py <suspect name>')
        return 1
    return check_answer_command(Path(__file__).resolve().parents[1], " ".join(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
"""
