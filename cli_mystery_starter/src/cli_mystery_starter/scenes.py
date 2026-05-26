"""Optional scene/beat engine.

Authors who want pacing — a story that opens, advances mid-game, and
closes — drop a `game/scenes.json` file:

    {
      "start": "discover_body",
      "scenes": [
        {
          "id": "discover_body",
          "narration": "The chandelier still swings.",
          "advances_to": "confront_butler",
          "advance_when": {
            "files_read":      ["game/incident"],
            "clues":           [],
            "suspects_marked": [],
            "topics_asked":    []
          }
        },
        {
          "id": "confront_butler",
          "narration": "You corner the butler in the East Hall.",
          "advances_to": null,
          "advance_when": {"clues": ["butler_alibi_break"]}
        }
      ]
    }

The engine starts the player in `start` and listens to the runtime
event bus. Whenever the current scene's `advance_when` predicates
are all satisfied, it transitions and prints the new scene's
narration. Final scenes (`advances_to: null`) do not auto-progress.

Predicates:
- `files_read`      every path must appear in the player's `visited` set
- `clues`           every clue id must be in the discovered set
- `suspects_marked` every name must have been `mark`-ed
- `topics_asked`    list of `"<npc>:<topic>"` pairs the player has asked

Loading is non-fatal; a malformed scenes file does not block play but
surfaces structural errors via `validate`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .events import EventBus


SCENES_FILENAME = "game/scenes.json"


@dataclass
class AdvanceWhen:
    files_read: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)
    suspects_marked: list[str] = field(default_factory=list)
    topics_asked: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.files_read or self.clues
                    or self.suspects_marked or self.topics_asked)

    def satisfied(self, state: "SceneState") -> bool:
        if any(p not in state.files_read for p in self.files_read):
            return False
        if any(c not in state.clues for c in self.clues):
            return False
        if any(s.lower() not in {x.lower() for x in state.suspects} for s in self.suspects_marked):
            return False
        if any(t not in state.topics for t in self.topics_asked):
            return False
        return True


@dataclass
class Scene:
    id: str
    narration: str = ""
    advances_to: str | None = None
    advance_when: AdvanceWhen = field(default_factory=AdvanceWhen)


@dataclass
class SceneState:
    files_read: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)
    suspects: set[str] = field(default_factory=set)
    topics: set[str] = field(default_factory=set)


def _parse_advance_when(raw: object, prefix: str, errors: list[str]) -> AdvanceWhen:
    if raw is None:
        return AdvanceWhen()
    if not isinstance(raw, dict):
        errors.append(f"{prefix}: `advance_when` must be an object")
        return AdvanceWhen()
    aw = AdvanceWhen()
    for field_name in ("files_read", "clues", "suspects_marked", "topics_asked"):
        value = raw.get(field_name, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append(f"{prefix}.advance_when.{field_name}: must be a list of strings")
            continue
        setattr(aw, field_name, list(value))
    return aw


def load_scenes(project_root: Path) -> tuple[list[Scene], str | None, list[str]]:
    """Returns `(scenes, start_id, errors)`."""
    path = project_root / SCENES_FILENAME
    if not path.exists():
        return [], None, []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], None, [f"{SCENES_FILENAME}: invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return [], None, [f"{SCENES_FILENAME}: top-level must be a JSON object"]

    errors: list[str] = []
    scenes_raw = data.get("scenes", [])
    if not isinstance(scenes_raw, list) or not scenes_raw:
        return [], None, [f"{SCENES_FILENAME}: `scenes` must be a non-empty list"]

    scenes: list[Scene] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(scenes_raw):
        prefix = f"{SCENES_FILENAME}.scenes[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        sid = item.get("id")
        narration = item.get("narration", "")
        advances_to = item.get("advances_to", None)
        if not isinstance(sid, str) or not sid:
            errors.append(f"{prefix}: missing/invalid `id`")
            continue
        if sid in seen_ids:
            errors.append(f"{prefix}: duplicate id {sid!r}")
            continue
        if not isinstance(narration, str):
            errors.append(f"{prefix}: `narration` must be a string")
            continue
        if advances_to is not None and not isinstance(advances_to, str):
            errors.append(f"{prefix}: `advances_to` must be a string or null")
            continue
        advance_when = _parse_advance_when(
            item.get("advance_when"), prefix, errors,
        )
        seen_ids.add(sid)
        scenes.append(Scene(id=sid, narration=narration,
                            advances_to=advances_to, advance_when=advance_when))

    if not scenes:
        return [], None, errors

    start = data.get("start", scenes[0].id)
    if not isinstance(start, str) or start not in seen_ids:
        errors.append(f"{SCENES_FILENAME}: `start` must reference an existing scene id")
        return [], None, errors

    # Validate every advances_to references a known scene.
    for scene in scenes:
        if scene.advances_to is not None and scene.advances_to not in seen_ids:
            errors.append(
                f"{SCENES_FILENAME}.scenes[{scene.id}]: "
                f"advances_to references unknown scene {scene.advances_to!r}"
            )

    if errors:
        return [], None, errors
    return scenes, start, []


class SceneRouter:
    """Tracks the current scene and advances based on event bus signals."""

    def __init__(self, scenes: list[Scene], start: str | None) -> None:
        self.scenes_by_id: dict[str, Scene] = {s.id: s for s in scenes}
        self.scenes = scenes
        self.start = start
        self.current: str | None = start
        self.state = SceneState()
        self._bus: EventBus | None = None

    @property
    def has_scenes(self) -> bool:
        return bool(self.scenes)

    def attach(self, bus: EventBus, *, initial: dict | None = None) -> None:
        if initial:
            cur = initial.get("current_scene")
            if isinstance(cur, str) and cur in self.scenes_by_id:
                self.current = cur
            for key, target in (
                ("files_read", self.state.files_read),
                ("clues", self.state.clues),
                ("suspects", self.state.suspects),
                ("topics", self.state.topics),
            ):
                seed = initial.get(key, [])
                if isinstance(seed, list):
                    target.update(str(x) for x in seed if isinstance(x, str))

        self._bus = bus
        bus.subscribe("file:read", self._on_file_read)
        bus.subscribe("clue:revealed", self._on_clue_revealed)
        bus.subscribe("suspect:marked", self._on_suspect_marked)
        bus.subscribe("dialogue:asked", self._on_dialogue_asked)

    def _on_file_read(self, payload: dict) -> None:
        self.state.files_read.add(payload.get("path", ""))
        self._maybe_advance()

    def _on_clue_revealed(self, payload: dict) -> None:
        self.state.clues.add(payload.get("id", ""))
        self._maybe_advance()

    def _on_suspect_marked(self, payload: dict) -> None:
        self.state.suspects.add(payload.get("name", ""))
        self._maybe_advance()

    def _on_dialogue_asked(self, payload: dict) -> None:
        self.state.topics.add(
            f"{payload.get('npc', '')}:{payload.get('topic', '')}"
        )
        self._maybe_advance()

    def seed_clues(self, discovered: set[str]) -> None:
        self.state.clues.update(discovered)

    def _maybe_advance(self) -> None:
        if self.current is None:
            return
        scene = self.scenes_by_id.get(self.current)
        if scene is None or scene.advances_to is None:
            return
        if scene.advance_when.is_empty():
            # No transition criteria → manual advance only
            return
        if scene.advance_when.satisfied(self.state):
            previous = self.current
            self.current = scene.advances_to
            new_scene = self.scenes_by_id.get(self.current)
            if self._bus is not None:
                self._bus.emit(
                    "scene:advanced",
                    {
                        "from": previous,
                        "to": self.current,
                        "narration": new_scene.narration if new_scene else "",
                    },
                )
            # Cascade: a fresh transition may itself be auto-advancable.
            self._maybe_advance()

    def describe_current(self) -> str:
        if self.current is None or not self.scenes_by_id:
            return "(no active scene)"
        scene = self.scenes_by_id.get(self.current)
        if scene is None:
            return f"(scene {self.current!r} not found)"
        lines = [f"Scene: {scene.id}"]
        if scene.narration:
            lines.append("")
            lines.append(scene.narration)
        if scene.advances_to is None:
            lines.append("")
            lines.append("(final scene)")
            return "\n".join(lines)
        if scene.advance_when.is_empty():
            lines.append("")
            lines.append(f"Next: {scene.advances_to}")
            return "\n".join(lines)
        lines.append("")
        lines.append(f"Advances to `{scene.advances_to}` when:")
        for kind, items, have in (
            ("files_read", scene.advance_when.files_read, self.state.files_read),
            ("clues", scene.advance_when.clues, self.state.clues),
            ("suspects_marked", scene.advance_when.suspects_marked,
             {s.lower() for s in self.state.suspects}),
            ("topics_asked", scene.advance_when.topics_asked, self.state.topics),
        ):
            for needed in items:
                check = needed.lower() if kind == "suspects_marked" else needed
                mark = "✓" if check in have else "·"
                lines.append(f"  [{mark}] {kind}: {needed}")
        return "\n".join(lines)

