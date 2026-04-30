"""Tests for scaffold, validation, and the contract that connects them."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ._helpers import DEFAULT_CONFIG, ScaffoldedCase, create_project, set_real_answer

from cli_mystery_starter import contract, runtime, validation
from cli_mystery_starter.cli import main
from cli_mystery_starter.config import MysteryConfig
from cli_mystery_starter.validation import validate_project


class InitTests(ScaffoldedCase):
    def test_init_creates_runtime_wrappers_and_stubs(self) -> None:
        target = self.root / "generated-case"
        result = main(["init", str(target)])
        self.assertEqual(result, 0)
        self.assertTrue((target / "play.py").exists())
        self.assertTrue((target / "tools" / "check_answer.py").exists())
        self.assertTrue((target / "game" / "logs" / "README.md").exists())
        self.assertTrue((target / "hints" / "hint4").exists())

    def test_scaffold_writes_gitignore_protecting_session_and_solution(self) -> None:
        gi = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".session.json", gi)
        self.assertIn("solution", gi)

    def test_scaffold_rejects_unsafe_folder_paths(self) -> None:
        bad_target = self.root / "evil-case"
        bad_config = dict(DEFAULT_CONFIG)
        bad_config["folders"] = ["../escape", "ok/folder"]
        with self.assertRaises(ValueError):
            create_project(bad_target, bad_config)


class ValidateTests(ScaffoldedCase):
    def test_validate_passes_on_fresh_scaffold(self) -> None:
        set_real_answer(self.target)
        self.assertEqual(validate_project(self.target), [])

    def test_validate_flags_default_placeholder_answer(self) -> None:
        errors = validate_project(self.target)
        self.assertTrue(
            any("placeholder" in err.lower() for err in errors),
            f"expected placeholder warning, got: {errors}",
        )

    def test_validate_fails_for_missing_hint_and_bad_hash(self) -> None:
        (self.target / "hints" / "hint4").unlink()
        (self.target / "encoded").write_text("not-a-hash\n", encoding="utf-8")
        errors = validate_project(self.target)
        self.assertIn("Missing required path: hints/hint4", errors)
        self.assertTrue(
            any("not a recognized answer format" in err for err in errors),
            f"expected unrecognized-format error, got: {errors}",
        )

    def test_validate_fails_for_insufficient_clues(self) -> None:
        (self.target / "game" / "incident").write_text(
            "Incident\nCLUE: one pivot only\n", encoding="utf-8"
        )
        errors = validate_project(self.target)
        self.assertIn(
            "`game/incident` should contain at least 3 clue markers `CLUE`",
            errors,
        )


class ContractTests(ScaffoldedCase):
    def test_contract_drives_validation_and_runtime_surfaces(self) -> None:
        self.assertEqual(set(validation.REQUIRED_PATHS),
                         set(contract.required_file_paths()))
        self.assertEqual(set(validation.EXPECTED_FOLDERS),
                         set(contract.expected_folders()))
        self.assertEqual(set(validation.EVIDENCE_FOLDERS),
                         set(contract.evidence_folders()))
        self.assertEqual(runtime.SURFACES, contract.surfaces_map())
        for must_have in ("README.md", "instructions", "encoded",
                          "play.py", "game/incident", "game/people"):
            self.assertIn(must_have, validation.REQUIRED_PATHS)


class CliTests(ScaffoldedCase):
    def test_check_answer_command_accepts_default_answer(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["check-answer", str(self.target), "John Doe"])
        self.assertEqual(result, 0)
        self.assertIn("Correct: John Doe", buffer.getvalue())

    def test_play_command_dispatches_to_runtime(self) -> None:
        with patch("cli_mystery_starter.cli.play_project", return_value=0) as mock_play:
            result = main(["play", str(self.target)])
        self.assertEqual(result, 0)
        mock_play.assert_called_once()


if __name__ == "__main__":
    unittest.main()
