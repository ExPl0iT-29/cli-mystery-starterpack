from __future__ import annotations

from pathlib import Path

from .runtime import check_answer, load_title, validate_runtime_project


def check_answer_command(project_root: Path, guess: str) -> int:
    errors = validate_runtime_project(project_root)
    if errors:
        for error in errors:
            print(error)
        return 1
    if check_answer(project_root, guess):
        print(f"Correct: {guess.strip()}")
        print(f"You solved {load_title(project_root)}.")
        return 0
    print("Incorrect.")
    return 2
