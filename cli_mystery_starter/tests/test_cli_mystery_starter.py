from __future__ import annotations

import hashlib
import io
import os
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


def _set_real_answer(target: Path, answer: str = "Maria Ortega") -> None:
    digest = hashlib.md5(answer.encode("utf-8"), usedforsecurity=False).hexdigest()
    (target / "encoded").write_text(digest + "\n", encoding="utf-8")


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
        _set_real_answer(target)
        errors = validate_project(target)
        self.assertEqual(errors, [])

    def test_validate_flags_default_placeholder_answer(self) -> None:
        target = self.scaffold_case()
        errors = validate_project(target)
        self.assertTrue(
            any("placeholder" in err.lower() for err in errors),
            f"expected placeholder warning, got: {errors}",
        )

    def test_scaffold_rejects_unsafe_folder_paths(self) -> None:
        target = self.root / "evil-case"
        bad_config = dict(DEFAULT_CONFIG)
        bad_config["folders"] = ["../escape", "ok/folder"]
        with self.assertRaises(ValueError):
            create_project(target, bad_config)

    def test_runtime_rejects_path_escape(self) -> None:
        target = self.scaffold_case()
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat ../../etc/passwd")
        self.assertIn("escapes the case file", buffer.getvalue())

    def test_runtime_rejects_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        target = self.scaffold_case()
        link_path = target / "game" / "shortcut"
        try:
            os.symlink(target / "game" / "incident", link_path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation not permitted")
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat shortcut")
        self.assertIn("Symlinks are not allowed", buffer.getvalue())

    def test_head_handles_non_integer_count(self) -> None:
        target = self.scaffold_case()
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("head incident abc")
        self.assertIn("Usage: head", buffer.getvalue())

    def test_open_handles_missing_surface_file(self) -> None:
        target = self.scaffold_case()
        (target / "game" / "incident").unlink()
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("open incident")
        out = buffer.getvalue()
        self.assertIn("incident", out)
        self.assertNotIn("Traceback", out)

    def test_eof_quits_cleanly(self) -> None:
        target = self.scaffold_case()
        shell = InvestigationShell(target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = shell.onecmd("EOF")
        self.assertTrue(result)
        self.assertIn("Case file closed", buffer.getvalue())

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
