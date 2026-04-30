from __future__ import annotations

import json
from pathlib import Path

from . import verifier


PLACEHOLDER_ANSWER = "John Doe"
DEFAULT_PROJECT_NAME = "my-cli-mystery"


from . import contract


# Derived from contract.CONTRACT; kept as module-level lists for back-compat
# with any external readers that imported these names.
REQUIRED_PATHS = contract.required_file_paths()
EXPECTED_FOLDERS = contract.expected_folders()
EVIDENCE_FOLDERS = contract.evidence_folders()


def validate_project(root: Path) -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            errors.append(f"Missing required path: {rel}")

    config_path = root / "mystery_config.json"
    config = None
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
                if incident_text.count(clue_marker) < 3:
                    errors.append(
                        f"`game/incident` should contain at least 3 clue markers `{clue_marker}`"
                    )
            folders = config.get("folders")
            if not isinstance(folders, list) or not all(isinstance(item, str) for item in folders):
                errors.append("`mystery_config.json` field `folders` must be a list of strings")
            else:
                for folder in folders:
                    if not (root / folder).exists():
                        errors.append(f"Configured folder is missing: {folder}")
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in mystery_config.json: {exc}")

    people_path = root / "game/people"
    if people_path.exists():
        text = people_path.read_text(encoding="utf-8").strip()
        lines = [line for line in text.splitlines() if line.strip()]
        if len(lines) < 2:
            errors.append("`game/people` should contain a header and at least one record")
        if lines:
            header = lines[0]
            if "|" not in header and "\t" not in header:
                errors.append("`game/people` header should use `|` or tab delimiters")

    encoded_path = root / "encoded"
    if encoded_path.exists():
        encoded = encoded_path.read_text(encoding="utf-8").strip()
        fmt = verifier.detect_format(encoded)
        if fmt is None:
            errors.append(
                "`encoded` is not a recognized answer format "
                "(expected `sha256$<salt>$<digest>` or a 32-char MD5 hex digest)"
            )
        elif verifier.verify(encoded, PLACEHOLDER_ANSWER):
            project_name = (config or {}).get("project_name") if config is not None else None
            if not project_name or project_name == DEFAULT_PROJECT_NAME:
                errors.append(
                    f"`encoded` still resolves to the placeholder `{PLACEHOLDER_ANSWER}` answer; "
                    "set a real answer before shipping (see `solution` for the one-liner)"
                )

    play_wrapper = root / "play.py"
    if play_wrapper.exists():
        text = play_wrapper.read_text(encoding="utf-8")
        if "play_project" not in text:
            errors.append("`play.py` should call `cli_mystery_starter.runtime.play_project`")

    answer_wrapper = root / "tools/check_answer.py"
    if answer_wrapper.exists():
        text = answer_wrapper.read_text(encoding="utf-8")
        if "check_answer_command" not in text:
            errors.append(
                "`tools/check_answer.py` should call `cli_mystery_starter.answer.check_answer_command`"
            )

    for folder in EXPECTED_FOLDERS:
        if not (root / folder).exists():
            errors.append(f"Missing expected folder: {folder}")

    for folder in EVIDENCE_FOLDERS:
        path = root / folder
        if path.exists() and path.is_dir():
            has_file = any(item.is_file() for item in path.rglob("*"))
            if not has_file:
                errors.append(f"Evidence folder should contain at least one file: {folder}")

    return errors
