from __future__ import annotations

import json
from pathlib import Path


REQUIRED_PATHS = [
    "README.md",
    "instructions",
    "solution",
    "encoded",
    "game/incident",
    "game/people",
    "design/story_bible.md",
    "design/clue_graph.md",
    "docs/data_schemas.md",
]


def validate_project(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            errors.append(f"Missing required path: {rel}")

    config_path = root / "mystery_config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            clue_marker = config.get("clue_marker", "CLUE")
            incident_path = root / "game/incident"
            if incident_path.exists():
                incident_text = incident_path.read_text(encoding="utf-8")
                if clue_marker not in incident_text:
                    errors.append(
                        f"`game/incident` does not contain the configured clue marker `{clue_marker}`"
                    )
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in mystery_config.json: {exc}")

    people_path = root / "game/people"
    if people_path.exists():
        text = people_path.read_text(encoding="utf-8").strip()
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            errors.append("`game/people` should contain a header and at least one record")

    return errors
