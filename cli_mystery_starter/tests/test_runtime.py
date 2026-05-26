"""Tests for the InvestigationShell runtime: shell verbs, paths, session."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.runtime import InvestigationShell


class ShellBasicsTests(ScaffoldedCase):
    def test_runtime_shell_can_read_and_accuse(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat incident")
            shell.onecmd("accuse John Doe")
        output = buffer.getvalue()
        self.assertIn("Incident Report", output)
        self.assertIn("Accusation accepted.", output)

    def test_help_topic_uses_docstring(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("help cat")
        self.assertIn("cat <path>", buffer.getvalue())

    def test_eof_quits_cleanly(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = shell.onecmd("EOF")
        self.assertTrue(result)
        self.assertIn("Case file closed", buffer.getvalue())


class ShellSafetyTests(ScaffoldedCase):
    def test_runtime_rejects_path_escape(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat ../../etc/passwd")
        self.assertIn("escapes the case file", buffer.getvalue())

    def test_runtime_rejects_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        link_path = self.target / "game" / "shortcut"
        try:
            os.symlink(self.target / "game" / "incident", link_path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation not permitted")
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat shortcut")
        self.assertIn("Symlinks are not allowed", buffer.getvalue())

    def test_head_handles_non_integer_count(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("head incident abc")
        self.assertIn("Usage: head", buffer.getvalue())

    def test_open_handles_missing_surface_file(self) -> None:
        (self.target / "game" / "incident").unlink()
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("open incident")
        out = buffer.getvalue()
        self.assertNotIn("Traceback", out)


class ShellSearchTests(ScaffoldedCase):
    def test_find_verb_lists_filename_matches(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("find hint /hints")
        output = buffer.getvalue()
        self.assertIn("hints/hint1", output)
        self.assertIn("hints/hint4", output)

    def test_grep_skips_binary_without_crashing(self) -> None:
        (self.target / "game" / "logs" / "blob.bin").write_bytes(b"\x00\x01\x02\xff\xfe")
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("grep placeholder logs")
        self.assertNotIn("Traceback", buffer.getvalue())

    def test_progress_reports_visited_files(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat incident")
            shell.onecmd("progress")
        self.assertRegex(buffer.getvalue(), r"Read 1/\d+ game files")


class SessionPersistenceTests(ScaffoldedCase):
    def test_session_persists_notes_and_suspects_across_runs(self) -> None:
        shell1 = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell1.onecmd("note Suspect was at the gala until midnight")
            shell1.onecmd("mark Maria Ortega")
            shell1.onecmd("cat incident")
            shell1.onecmd("quit")
        self.assertTrue((self.target / ".session.json").exists())
        shell2 = InvestigationShell(self.target)
        self.assertEqual(shell2.case_notes,
                         ["Suspect was at the gala until midnight"])
        self.assertEqual(shell2.suspects, ["Maria Ortega"])
        self.assertIn("game/incident", shell2.visited)

    def test_session_ignores_corrupt_state(self) -> None:
        (self.target / ".session.json").write_text("{not json", encoding="utf-8")
        shell = InvestigationShell(self.target)
        self.assertEqual(shell.case_notes, [])
        self.assertEqual(shell.suspects, [])

    def test_journal_recaps_progress(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat incident")
            shell.onecmd("note check chandelier")
            shell.onecmd("mark Maria")
            shell.onecmd("journal")
        out = buffer.getvalue()
        self.assertIn("game/incident", out)
        self.assertIn("Maria", out)
        self.assertIn("check chandelier", out)


if __name__ == "__main__":
    unittest.main()
