"""Optional NPC dialogue / interview system.

Authors who want a "probe a witness" experience drop one JSON file per
NPC under `game/dialogue/<slug>.json`:

    {
      "name": "The Butler",
      "greeting": "I served the family for thirty years.",
      "topics": [
        {
          "id": "chandelier",
          "summary": "the chandelier",
          "requires_clues": [],
          "response": "I oiled it last Tuesday.",
          "reveals_clue": "butler_alibi_break"
        },
        {
          "id": "midnight",
          "summary": "the midnight gap",
          "requires_clues": ["butler_alibi_break"],
          "response": "Fine. I was in the cellar.",
          "reveals_clue": "butler_in_cellar"
        }
      ]
    }

Player UX:

    ask butler                       # lists currently-available topics
    ask butler about chandelier      # prints the response, may reveal a clue

Topics are gated on the player's `discovered` clue set, so investigation
order matters: the butler will not discuss "the midnight gap" until the
player has surfaced the alibi break.

Loading is non-fatal: missing or malformed files do not break play;
structural errors surface only via `validate`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


DIALOGUE_DIRNAME = "game/dialogue"


@dataclass
class Topic:
    id: str
    summary: str
    response: str
    requires_clues: list[str] = field(default_factory=list)
    reveals_clue: str | None = None

    def is_available(self, discovered_clues: set[str]) -> bool:
        return all(req in discovered_clues for req in self.requires_clues)


@dataclass
class NPC:
    slug: str
    name: str
    greeting: str
    topics: list[Topic] = field(default_factory=list)

    def topic(self, topic_id: str) -> Topic | None:
        for topic in self.topics:
            if topic.id == topic_id:
                return topic
        return None


def _slug_from_filename(path: Path) -> str:
    return path.stem.lower()


def load_dialogue(project_root: Path) -> tuple[dict[str, NPC], list[str]]:
    """Load every `game/dialogue/*.json` file.

    Returns `({slug: NPC}, errors)`. Slugs are derived from the file
    stem and normalized to lowercase. An empty/missing directory is
    treated as "no dialogue declared" — not an error.
    """
    base = project_root / DIALOGUE_DIRNAME
    if not base.exists() or not base.is_dir():
        return {}, []

    npcs: dict[str, NPC] = {}
    errors: list[str] = []

    for path in sorted(base.glob("*.json")):
        slug = _slug_from_filename(path)
        prefix = f"{DIALOGUE_DIRNAME}/{path.name}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{prefix}: invalid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{prefix}: top-level must be a JSON object")
            continue

        name = data.get("name", slug.replace("_", " ").title())
        greeting = data.get("greeting", "")
        topics_raw = data.get("topics", [])
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{prefix}: invalid `name`")
            continue
        if not isinstance(greeting, str):
            errors.append(f"{prefix}: invalid `greeting`")
            continue
        if not isinstance(topics_raw, list):
            errors.append(f"{prefix}: `topics` must be a list")
            continue

        topics: list[Topic] = []
        seen_topic_ids: set[str] = set()
        for index, item in enumerate(topics_raw):
            tprefix = f"{prefix}.topics[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{tprefix}: must be an object")
                continue
            tid = item.get("id")
            summary = item.get("summary", "")
            response = item.get("response", "")
            requires = item.get("requires_clues", [])
            reveals = item.get("reveals_clue")
            if not isinstance(tid, str) or not tid:
                errors.append(f"{tprefix}: missing/invalid `id`")
                continue
            if tid in seen_topic_ids:
                errors.append(f"{tprefix}: duplicate id {tid!r}")
                continue
            if not isinstance(summary, str):
                errors.append(f"{tprefix}: invalid `summary`")
                continue
            if not isinstance(response, str) or not response.strip():
                errors.append(f"{tprefix}: missing/invalid `response`")
                continue
            if not isinstance(requires, list) or not all(
                isinstance(r, str) for r in requires
            ):
                errors.append(f"{tprefix}: `requires_clues` must be a list of strings")
                continue
            if reveals is not None and not isinstance(reveals, str):
                errors.append(f"{tprefix}: `reveals_clue` must be a string if present")
                continue
            seen_topic_ids.add(tid)
            topics.append(Topic(
                id=tid,
                summary=summary or tid,
                response=response,
                requires_clues=list(requires),
                reveals_clue=reveals or None,
            ))

        npcs[slug] = NPC(slug=slug, name=name, greeting=greeting, topics=topics)

    return npcs, errors
