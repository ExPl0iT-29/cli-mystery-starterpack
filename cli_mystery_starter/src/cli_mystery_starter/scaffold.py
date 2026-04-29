from __future__ import annotations

import json
from pathlib import Path

from . import templates


DEFAULT_CONFIG = {
    "project_name": "my-cli-mystery",
    "display_title": "My CLI Mystery",
    "theme": "original mystery",
    "player_role": "investigator",
    "answer_type": "culprit_name",
    "clue_marker": "CLUE",
    "folders": [
        "game/interviews",
        "game/locations",
        "game/memberships",
        "game/logs",
        "game/registry",
        "hints",
        "docs",
        "design",
        "tools",
    ],
}


def load_config(config_path: Path | None) -> dict:
    if config_path is None:
        return dict(DEFAULT_CONFIG)
    with config_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    merged = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


def ensure_clean_target(target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        raise ValueError(f"Target directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_project(target: Path, config: dict) -> list[Path]:
    ensure_clean_target(target)

    for folder in config["folders"]:
        (target / folder).mkdir(parents=True, exist_ok=True)

    project_name = templates.slugify(config["project_name"])
    display_title = config["display_title"]
    clue_marker = config["clue_marker"]

    files: dict[str, str] = {
        "README.md": templates.root_readme(project_name, display_title),
        "instructions": templates.instructions(display_title),
        "solution": templates.solution(),
        "encoded": templates.default_answer_hash("John Doe") + "\n",
        "play.py": templates.play_wrapper(),
        "game/incident": templates.incident(clue_marker),
        "game/people": templates.people(),
        "game/interviews/README.md": templates.family_stub(
            "Interviews", "Store one witness or suspect interview per file."
        ),
        "game/locations/East_Hall": templates.location_stub("East_Hall"),
        "game/locations/North_Wing": templates.location_stub("North_Wing"),
        "game/locations/South_Annex": templates.location_stub("South_Annex"),
        "game/memberships/README.md": templates.family_stub(
            "Memberships", "Use rosters or social linkage files to narrow suspects."
        ),
        "game/logs/README.md": templates.family_stub(
            "Logs", "Record timestamps, access traces, and operational truth."
        ),
        "game/registry/README.md": templates.family_stub(
            "Registry", "Store structured records tied to motive or access."
        ),
        "hints/hint1": templates.hint(1),
        "hints/hint2": templates.hint(2),
        "hints/hint3": templates.hint(3),
        "hints/hint4": templates.hint(4),
        "design/story_bible.md": templates.story_bible(
            display_title, config["theme"], config["player_role"]
        ),
        "design/clue_graph.md": templates.clue_graph(),
        "docs/data_schemas.md": templates.data_schemas(),
        "docs/notes.md": "# Notes\n\nKeep author notes here.\n",
        "tools/README.md": "# Tools\n\n- `check_answer.py`: verify a suspect name against the encoded answer.\n",
        "tools/check_answer.py": templates.answer_wrapper(),
        "mystery_config.json": json.dumps(config, indent=2) + "\n",
    }

    written: list[Path] = []
    for relative, content in files.items():
        path = target / relative
        write_text(path, content)
        written.append(path)
    return written
