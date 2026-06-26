"""Single source of truth for the on-disk shape of a mystery project.

`scaffold`, `validation`, and `runtime` all derive their per-path knowledge
from `CONTRACT` so that adding a new evidence family, required file, or
shell `open` surface is a one-line change here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Surface:
    """A required path in a mystery project.

    `key` exposes this path under `open <key>` in the runtime shell;
    `None` means the path is required but not a shell shortcut.
    """

    key: str | None
    rel_path: tuple[str, ...]
    kind: Literal["file", "dir"]
    required: bool = True
    is_evidence: bool = False  # directories that must contain >=1 file


CONTRACT: tuple[Surface, ...] = (
    # Game-content files exposed via `open`
    Surface("incident", ("game", "incident"), "file"),
    Surface("people", ("game", "people"), "file"),
    # Evidence directories exposed via `open`
    Surface("logs", ("game", "logs"), "dir", is_evidence=True),
    Surface("interviews", ("game", "interviews"), "dir", is_evidence=True),
    Surface("locations", ("game", "locations"), "dir", is_evidence=True),
    Surface("registry", ("game", "registry"), "dir", is_evidence=True),
    Surface("memberships", ("game", "memberships"), "dir", is_evidence=True),
    # Other directories exposed via `open`
    Surface("hints", ("hints",), "dir"),
    Surface("design", ("design",), "dir"),
    # Required files (not shell surfaces)
    Surface(None, ("README.md",), "file"),
    Surface(None, ("instructions",), "file"),
    Surface(None, ("solution",), "file"),
    Surface(None, ("encoded",), "file"),
    Surface(None, ("play.py",), "file"),
    Surface(None, ("hints", "hint1"), "file"),
    Surface(None, ("hints", "hint2"), "file"),
    Surface(None, ("hints", "hint3"), "file"),
    Surface(None, ("hints", "hint4"), "file"),
    Surface(None, ("design", "story_bible.md"), "file"),
    Surface(None, ("design", "clue_graph.md"), "file"),
    Surface(None, ("docs", "data_schemas.md"), "file"),
    Surface(None, ("tools", "check_answer.py"), "file"),
    # Required directories without `open` shortcuts
    Surface(None, ("docs",), "dir"),
    Surface(None, ("tools",), "dir"),
)


def rel(surface: Surface) -> str:
    return "/".join(surface.rel_path)


def required_file_paths() -> list[str]:
    return [rel(s) for s in CONTRACT if s.required and s.kind == "file"]


def expected_folders() -> list[str]:
    return [rel(s) for s in CONTRACT if s.required and s.kind == "dir"]


def evidence_folders() -> list[str]:
    return [rel(s) for s in CONTRACT if s.is_evidence]


def surfaces_map() -> dict[str, tuple[str, ...]]:
    return {s.key: s.rel_path for s in CONTRACT if s.key}
