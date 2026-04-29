from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from cli_mystery_starter.cli import main
from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.scaffold import DEFAULT_CONFIG, create_project
from cli_mystery_starter.validation import validate_project


class StarterPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def scaffold_case(self, name: str = "case") -> Path:
        target = self.root / name
        create_project(target, dict(DEFAULT_CONFIG))
        return target

    def test_init_creates_runtime_wrappers_and_stubs(self) -> None:
        target = self.root / "generated-case"
        result = main(["init", str(target)])
        self.assertEqual(result, 0)
        self.assertTrue((target / "play.py").exists())
        self.assertTrue((target / "tools" / "check_answer.py").exists())
        self.assertTrue((target / "game" / "logs" / "README.md").exists())
        self.assertTrue((target / "hints" / "hint4").exists())

    def test_validate_passes_on_fresh_scaffold(self) -> None:
        target = self.scaffold_case()
        errors = validate_project(target)
        self.assertEqual(errors, [])

    def test_validate_fails_for_missing_hint_and_bad_hash(self) -> None:
        target = self.scaffold_case()
        (target / "hints" / "hint4").unlink()
        (target / "encoded").write_text("not-a-hash\n", encoding="utf-8")
        errors = validate_project(target)
        self.assertIn("Missing required path: hints/hint4", errors)
        self.assertIn("`encoded` must contain a lowercase 32-character MD5 hex digest", errors)

    def test_validate_fails_for_insufficient_clues(self) -> None:
        target = self.scaffold_case()
        (target / "game" / "incident").write_text(
            "Incident\nCLUE: one pivot only\n",
            encoding="utf-8",
        )
        errors = validate_project(target)
        self.assertIn("`game/incident` should contain at least 3 clue markers `CLUE`", errors)

    def test_check_answer_command_accepts_default_answer(self) -> None:
        target = self.scaffold_case()
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["check-answer", str(target), "John Doe"])
        self.assertEqual(result, 0)
        self.assertIn("Correct: John Doe", buffer.getvalue())

    def test_play_command_dispatches_to_runtime(self) -> None:
        target = self.scaffold_case()
        with patch("cli_mystery_starter.cli.play_project", return_value=0) as mock_play:
            result = main(["play", str(target)])
        self.assertEqual(result, 0)
        mock_play.assert_called_once()

    def test_runtime_shell_can_read_and_accuse(self) -> None:
        target = self.scaffold_case()
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat incident")
            shell.onecmd("accuse John Doe")
        output = buffer.getvalue()
        self.assertIn("Incident Report", output)
        self.assertIn("Accusation accepted.", output)


if __name__ == "__main__":
    unittest.main()
