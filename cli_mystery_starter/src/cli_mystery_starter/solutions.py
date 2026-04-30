"""Optional multi-field, multi-ending solution model.

Authors can replace the binary right/wrong `encoded` flow with a richer
`solutions.json` at the project root:

    {
      "answers": {
        "culprit": {"value": "Maria Ortega", "aliases": ["Ortega"]},
        "motive":  {"value": "inheritance"},
        "weapon":  {"value": "chandelier"}
      },
      "endings": [
        {"id": "full_solve", "requires": ["culprit", "motive", "weapon"],
         "text": "You proved every piece of the case."},
        {"id": "partial",    "requires": ["culprit"],
         "text": "You named the right person but missed the why."}
      ]
    }

Players can submit either the legacy form (`accuse Maria Ortega` —
treated as `culprit=...`) or a multi-field form
(`accuse culprit="Maria Ortega" motive=inheritance`). The first
ending whose `requires` are all matched fires.

Field matching is case-insensitive and whitespace-collapsing; aliases
let authors accept multiple canonical spellings.

When `solutions.json` is absent the runtime falls back to the original
`encoded`-based check, so this is fully opt-in.
"""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, field
from pathlib import Path


SOLUTIONS_FILENAME = "solutions.json"


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


@dataclass
class FieldSpec:
    value: str
    aliases: list[str] = field(default_factory=list)

    def matches(self, guess: str) -> bool:
        canon = {_norm(self.value), *(_norm(a) for a in self.aliases)}
        return _norm(guess) in canon


@dataclass
class Ending:
    id: str
    requires: list[str]
    text: str = ""


@dataclass
class Solutions:
    fields: dict[str, FieldSpec]
    endings: list[Ending]

    def evaluate(self, guesses: dict[str, str]) -> tuple[set[str], Ending | None]:
        correct = {
            key for key, guess in guesses.items()
            if key in self.fields and self.fields[key].matches(guess)
        }
        for ending in self.endings:
            if all(req in correct for req in ending.requires):
                return correct, ending
        return correct, None


def parse_accusation(arg: str) -> dict[str, str]:
    """Turn an `accuse` argument into a `{field: guess}` map.

    `accuse Maria Ortega`                      -> {"culprit": "Maria Ortega"}
    `accuse culprit="Maria Ortega" motive=...` -> {"culprit": ..., "motive": ...}
    """
    raw = arg.strip()
    if not raw:
        return {}
    try:
        parts = shlex.split(raw)
    except ValueError:
        parts = raw.split()
    if parts and all("=" in p for p in parts):
        out: dict[str, str] = {}
        for token in parts:
            key, _, value = token.partition("=")
            key = key.strip()
            value = value.strip()
            if key:
                out[key] = value
        return out
    return {"culprit": raw}


def load_solutions(project_root: Path) -> tuple[Solutions | None, list[str]]:
    """Load `solutions.json` if present.

    Returns `(solutions, errors)`. `solutions` is `None` when the file
    is absent or fatally malformed. `errors` is non-empty whenever the
    file exists and has structural problems.
    """
    path = project_root / SOLUTIONS_FILENAME
    if not path.exists():
        return None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{SOLUTIONS_FILENAME}: invalid JSON: {exc}"]

    errors: list[str] = []
    if not isinstance(data, dict):
        return None, [f"{SOLUTIONS_FILENAME}: top-level must be a JSON object"]

    answers = data.get("answers")
    if not isinstance(answers, dict) or not answers:
        return None, [f"{SOLUTIONS_FILENAME}: `answers` must be a non-empty object"]

    fields: dict[str, FieldSpec] = {}
    for key, spec in answers.items():
        if not isinstance(spec, dict):
            errors.append(f"{SOLUTIONS_FILENAME}.answers.{key}: must be an object")
            continue
        value = spec.get("value")
        aliases = spec.get("aliases", [])
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{SOLUTIONS_FILENAME}.answers.{key}: missing/invalid `value`")
            continue
        if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
            errors.append(f"{SOLUTIONS_FILENAME}.answers.{key}: `aliases` must be a list of strings")
            continue
        fields[key] = FieldSpec(value=value, aliases=list(aliases))

    endings_raw = data.get("endings", [])
    if not isinstance(endings_raw, list):
        errors.append(f"{SOLUTIONS_FILENAME}: `endings` must be a list")
        endings_raw = []
    if not endings_raw:
        # Synthesize a default "full" ending requiring every field
        endings = [Ending(id="solve", requires=list(fields.keys()),
                          text="You completed every part of the case.")]
    else:
        endings = []
        for index, item in enumerate(endings_raw):
            prefix = f"{SOLUTIONS_FILENAME}.endings[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix}: must be an object")
                continue
            eid = item.get("id")
            req = item.get("requires", [])
            text = item.get("text", "")
            if not isinstance(eid, str) or not eid:
                errors.append(f"{prefix}: missing/invalid `id`")
                continue
            if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
                errors.append(f"{prefix}: `requires` must be a list of strings")
                continue
            for r in req:
                if r not in fields:
                    errors.append(f"{prefix}: requires unknown field {r!r}")
            if not isinstance(text, str):
                errors.append(f"{prefix}: `text` must be a string")
                continue
            endings.append(Ending(id=eid, requires=list(req), text=text))

    if errors:
        return None, errors
    return Solutions(fields=fields, endings=endings), []
