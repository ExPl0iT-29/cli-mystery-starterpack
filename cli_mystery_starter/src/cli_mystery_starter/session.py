"""Per-project session state: notes, suspects, and visited files.

Persisted to `<project_root>/.session.json` so progress survives between
runs of `play`. Authors should add `.session.json` to `.gitignore` so
multiple players do not collide on shared cases.

Atomic writes (`tmp + os.replace`) protect against partial writes if the
process is killed mid-save.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable


class SessionStore:
    SCHEMA_VERSION = 3
    SUPPORTED_VERSIONS = (1, 2, 3)
    FILENAME = ".session.json"

    @classmethod
    def path_for(cls, project_root: Path) -> Path:
        return project_root / cls.FILENAME

    @classmethod
    def load(cls, project_root: Path) -> dict:
        path = cls.path_for(project_root)
        if not path.exists():
            return cls._empty()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls._empty()
        if not isinstance(data, dict) or data.get("version") not in cls.SUPPORTED_VERSIONS:
            return cls._empty()
        current_scene = data.get("current_scene")
        return {
            "notes": [str(n) for n in data.get("notes", []) if isinstance(n, str)],
            "suspects": [str(s) for s in data.get("suspects", []) if isinstance(s, str)],
            "visited": [str(v) for v in data.get("visited", []) if isinstance(v, str)],
            "discovered_clues": [
                str(c) for c in data.get("discovered_clues", []) if isinstance(c, str)
            ],
            "topics_asked": [
                str(t) for t in data.get("topics_asked", []) if isinstance(t, str)
            ],
            "current_scene": current_scene if isinstance(current_scene, str) else None,
        }

    @classmethod
    def save(
        cls,
        project_root: Path,
        *,
        notes: Iterable[str],
        suspects: Iterable[str],
        visited: Iterable[str],
        discovered_clues: Iterable[str] = (),
        topics_asked: Iterable[str] = (),
        current_scene: str | None = None,
    ) -> None:
        payload = {
            "version": cls.SCHEMA_VERSION,
            "notes": list(notes),
            "suspects": list(suspects),
            "visited": sorted(set(visited)),
            "discovered_clues": sorted(set(discovered_clues)),
            "topics_asked": sorted(set(topics_asked)),
            "current_scene": current_scene,
        }
        path = cls.path_for(project_root)
        tmp = path.parent / (path.name + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    @staticmethod
    def _empty() -> dict:
        return {
            "notes": [], "suspects": [], "visited": [],
            "discovered_clues": [], "topics_asked": [], "current_scene": None,
        }
