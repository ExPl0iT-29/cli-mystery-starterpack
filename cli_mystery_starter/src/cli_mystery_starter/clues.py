"""Optional clue object model.

Authors who want a structured "clue collected" experience can drop a
`game/clues.json` file at their project root with a list of clue objects:

    [
      {
        "id": "ledger_entry_44",
        "title": "Mismatched signature in the East Hall ledger",
        "source_path": "game/registry/ledger.txt",
        "tags": ["timeline", "alibi:butler"]
      }
    ]

When the player `cat`s the matching `source_path`, the clue is
auto-marked as discovered and the `clues` shell verb lists what they
have collected so far. Discovery state is persisted in `.session.json`
so progress survives between runs.

Loading is non-fatal: a missing or malformed `clues.json` does not
break the runtime; structural errors surface only via `validate`.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .events import EventBus


CLUES_FILENAME = "game/clues.json"


@dataclass
class Clue:
    id: str
    title: str
    source_path: str
    tags: list[str] = field(default_factory=list)


def load_clues(project_root: Path) -> tuple[list[Clue], list[str]]:
    """Load `game/clues.json` if present.

    Returns `(clues, errors)`. `errors` is empty when the file is absent
    or fully valid; a non-empty `errors` list signals a structural
    problem the validator should report.
    """
    path = project_root / CLUES_FILENAME
    if not path.exists():
        return [], []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"{CLUES_FILENAME}: invalid JSON: {exc}"]
    if not isinstance(data, list):
        return [], [f"{CLUES_FILENAME}: top-level must be a JSON array"]

    clues: list[Clue] = []
    errors: list[str] = []
    seen_ids: set[str] = set()

    for index, item in enumerate(data):
        prefix = f"{CLUES_FILENAME}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: entry must be an object")
            continue
        cid = item.get("id")
        title = item.get("title")
        source = item.get("source_path")
        tags = item.get("tags", [])
        if not isinstance(cid, str) or not cid:
            errors.append(f"{prefix}: missing/invalid `id`")
            continue
        if cid in seen_ids:
            errors.append(f"{prefix}: duplicate id {cid!r}")
            continue
        if not isinstance(title, str) or not title:
            errors.append(f"{prefix}: missing/invalid `title`")
            continue
        if not isinstance(source, str) or not source:
            errors.append(f"{prefix}: missing/invalid `source_path`")
            continue
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            errors.append(f"{prefix}: `tags` must be a list of strings")
            continue
        seen_ids.add(cid)
        clues.append(Clue(id=cid, title=title, source_path=source, tags=list(tags)))

    return clues, errors


class ClueRegistry:
    """Tracks discovered clues and reacts to `file:read` events."""

    def __init__(self, clues: list[Clue]) -> None:
        self.clues = clues
        self._by_path: dict[str, list[Clue]] = defaultdict(list)
        for clue in clues:
            self._by_path[clue.source_path].append(clue)
        self.discovered: set[str] = set()
        self._bus: EventBus | None = None

    def attach(self, bus: EventBus, *, initial: list[str] | None = None) -> None:
        valid_ids = {c.id for c in self.clues}
        if initial:
            self.discovered = {cid for cid in initial if cid in valid_ids}
        self._bus = bus
        bus.subscribe("file:read", self._on_file_read)

    def _on_file_read(self, payload: dict) -> None:
        path = payload.get("path", "")
        for clue in self._by_path.get(path, ()):
            if clue.id not in self.discovered:
                self.discovered.add(clue.id)
                if self._bus is not None:
                    self._bus.emit(
                        "clue:revealed",
                        {"id": clue.id, "via": f"file:{path}"},
                    )

    def discovered_clues(self) -> list[Clue]:
        return [c for c in self.clues if c.id in self.discovered]
