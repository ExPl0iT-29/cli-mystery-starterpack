"""Tests for the optional scene/beat engine."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.scenes import (
    AdvanceWhen,
    SceneState,
    load_scenes,
)
from cli_mystery_starter.validation import validate_project


SCENES = {
    "start": "discover",
    "scenes": [
        {
            "id": "discover",
            "narration": "The chandelier still swings.",
            "advances_to": "confront",
            "advance_when": {"files_read": ["game/incident"]},
        },
        {
            "id": "confront",
            "narration": "You corner the butler in the East Hall.",
            "advances_to": "verdict",
            "advance_when": {"clues": ["butler_alibi_break"]},
        },
        {
            "id": "verdict",
            "narration": "Time for the accusation.",
            "advances_to": None,
        },
    ],
}


class AdvanceWhenTests(unittest.TestCase):
    def test_satisfied_with_all_predicates(self) -> None:
        aw = AdvanceWhen(files_read=["a"], clues=["c"], suspects_marked=["S"])
        state = SceneState(
            files_read={"a"}, clues={"c"}, suspects={"s"}, topics=set()
        )
        self.assertTrue(aw.satisfied(state))

    def test_unsatisfied_when_missing_clue(self) -> None:
        aw = AdvanceWhen(clues=["c1", "c2"])
        state = SceneState(clues={"c1"})
        self.assertFalse(aw.satisfied(state))

    def test_suspects_match_is_case_insensitive(self) -> None:
        aw = AdvanceWhen(suspects_marked=["Maria Ortega"])
        state = SceneState(suspects={"maria ortega"})
        self.assertTrue(aw.satisfied(state))


class LoadScenesTests(ScaffoldedCase):
    def _seed(self, payload: dict) -> None:
        (self.target / "game" / "scenes.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_absent_file_returns_empty(self) -> None:
        scenes, start, errors = load_scenes(self.target)
        self.assertEqual(scenes, [])
        self.assertIsNone(start)
        self.assertEqual(errors, [])

    def test_well_formed_loads(self) -> None:
        self._seed(SCENES)
        scenes, start, errors = load_scenes(self.target)
        self.assertEqual(errors, [])
        self.assertEqual(start, "discover")
        self.assertEqual([s.id for s in scenes], ["discover", "confront", "verdict"])

    def test_invalid_json_reported(self) -> None:
        (self.target / "game" / "scenes.json").write_text("{not", encoding="utf-8")
        _, _, errors = load_scenes(self.target)
        self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_unknown_advances_to_reported(self) -> None:
        self._seed({
            "scenes": [
                {"id": "a", "advances_to": "ghost"},
            ],
        })
        _, _, errors = load_scenes(self.target)
        self.assertTrue(any("ghost" in e for e in errors))

    def test_unknown_start_reported(self) -> None:
        self._seed({
            "start": "ghost",
            "scenes": [{"id": "a"}],
        })
        _, _, errors = load_scenes(self.target)
        self.assertTrue(any("start" in e for e in errors))

    def test_validate_surfaces_scene_errors(self) -> None:
        (self.target / "game" / "scenes.json").write_text(
            json.dumps({"scenes": "not a list"}), encoding="utf-8"
        )
        errors = validate_project(self.target)
        self.assertTrue(any("scenes.json" in e for e in errors))


class ShellSceneTests(ScaffoldedCase):
    def setUp(self) -> None:
        super().setUp()
        (self.target / "game" / "scenes.json").write_text(
            json.dumps(SCENES), encoding="utf-8"
        )
        # Also declare a clue so the second-scene advance gate is reachable.
        (self.target / "game" / "clues.json").write_text(
            json.dumps([
                {"id": "butler_alibi_break", "title": "x",
                 "source_path": "game/people", "tags": []},
            ]),
            encoding="utf-8",
        )

    def test_scene_verb_shows_current(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("scene")
        out = buffer.getvalue()
        self.assertIn("discover", out)
        self.assertIn("game/incident", out)

    def test_reading_required_file_advances_scene(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat incident")
        out = buffer.getvalue()
        self.assertIn("confront", out)
        self.assertEqual(shell.scene_router.current, "confront")

    def test_clue_revelation_advances_to_final(self) -> None:
        shell = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell.onecmd("cat incident")            # discover -> confront
            shell.onecmd("cat people")              # discovers butler_alibi_break
        # confront's advance_when is on the clue; cat people emits both
        # file:read and clue:revealed (via ClueRegistry)
        self.assertEqual(shell.scene_router.current, "verdict")

    def test_final_scene_does_not_auto_advance(self) -> None:
        shell = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell.onecmd("cat incident")
            shell.onecmd("cat people")
        # In `verdict` (final), additional events should not transition further
        self.assertEqual(shell.scene_router.current, "verdict")

    def test_current_scene_persists_across_runs(self) -> None:
        shell1 = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell1.onecmd("cat incident")
            shell1.onecmd("quit")
        shell2 = InvestigationShell(self.target)
        self.assertEqual(shell2.scene_router.current, "confront")


if __name__ == "__main__":
    unittest.main()
