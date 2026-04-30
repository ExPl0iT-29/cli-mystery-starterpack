"""Typed configuration schema for `mystery_config.json`.

`MysteryConfig.from_dict` rejects unknown keys, type-checks fields, and
enforces folder-path safety. Schema bumps go here; `contract_version`
lets validators detect old-vs-new project shapes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import verifier


CONTRACT_VERSION = 2  # bump when on-disk shape changes incompatibly


@dataclass
class MysteryConfig:
    project_name: str = "my-cli-mystery"
    display_title: str = "My CLI Mystery"
    theme: str = "original mystery"
    player_role: str = "investigator"
    clue_marker: str = "CLUE"
    answer_format: str = verifier.FORMAT_SHA256_SALTED
    hint_count: int = 4
    contract_version: int = CONTRACT_VERSION
    folders: list[str] = field(
        default_factory=lambda: [
            "game/interviews",
            "game/locations",
            "game/memberships",
            "game/logs",
            "game/registry",
            "hints",
            "docs",
            "design",
            "tools",
        ]
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MysteryConfig":
        if not isinstance(data, dict):
            raise ValueError("Config root must be a JSON object.")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        unknown = set(data) - known
        if unknown:
            raise ValueError(
                f"Unknown config keys: {sorted(unknown)}. "
                f"Known keys: {sorted(known)}."
            )
        merged = cls()
        for key, value in data.items():
            expected = type(getattr(merged, key))
            # Allow int where bool would coerce; otherwise enforce type.
            if expected is list and not isinstance(value, list):
                raise ValueError(f"Config key {key!r} must be a list, got {type(value).__name__}.")
            if expected is str and not isinstance(value, str):
                raise ValueError(f"Config key {key!r} must be a string, got {type(value).__name__}.")
            if expected is int and not isinstance(value, int):
                raise ValueError(f"Config key {key!r} must be an integer, got {type(value).__name__}.")
            setattr(merged, key, value)

        if merged.answer_format not in verifier.KNOWN_FORMATS:
            raise ValueError(
                f"answer_format {merged.answer_format!r} not supported; "
                f"expected one of {verifier.KNOWN_FORMATS}."
            )
        if merged.hint_count < 1:
            raise ValueError("hint_count must be >= 1.")
        if not merged.clue_marker.strip():
            raise ValueError("clue_marker must be a non-empty, non-whitespace string.")
        for folder in merged.folders:
            if not isinstance(folder, str):
                raise ValueError(f"folders entries must be strings; got {folder!r}.")
            p = Path(folder)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"Unsafe folder path: {folder!r}")
        return merged

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
