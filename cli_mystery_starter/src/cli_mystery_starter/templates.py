from __future__ import annotations

from hashlib import md5


def slugify(value: str) -> str:
    return "-".join(part for part in value.strip().lower().replace("_", " ").split() if part)


def default_answer_hash(answer: str) -> str:
    return md5(answer.encode("utf-8")).hexdigest()


def root_readme(project_name: str, display_title: str) -> str:
    return f"""# {display_title}

`{project_name}` is a filesystem-based CLI mystery game scaffolded from `cli_mystery_starter`.

## Start Here

1. Open `instructions`
2. Enter the `game/` folder
3. Inspect `incident`
4. Use shell commands to follow the clue graph

## Authoring

Edit these first:

- `design/story_bible.md`
- `design/clue_graph.md`
- `docs/data_schemas.md`
- `game/incident`

Run validation with:

```bash
python -m cli_mystery_starter validate .
```
"""


def instructions(display_title: str) -> str:
    return f"""Welcome to {display_title}.

Start by entering the `game` directory and reading the `incident` file.

Important notes:

- the real clues are marked with `CLUE`
- if you get stuck, read the files in `hints/`
- to check your answer, read `solution`
- do not start by opening every file manually; search and cross-reference them
"""


def solution() -> str:
    return """Checking Your Answer
====================

Replace `John Doe` with your suspected answer:

    echo "John Doe" | python -c "import sys,hashlib; print(hashlib.md5(sys.stdin.read().strip().encode()).hexdigest())"

Compare the output against the contents of `encoded`.

Author note:
- replace the placeholder encoded hash before shipping
- optionally add a platform-specific helper script later
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
