"""Tests for the optional NPC dialogue system."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.dialogue import Topic, load_dialogue
from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.validation import validate_project


BUTLER = {
    "name": "The Butler",
    "greeting": "I served the family for thirty years.",
    "topics": [
        {
            "id": "chandelier",
            "summary": "the chandelier",
            "response": "I oiled it last Tuesday.",
            "reveals_clue": "butler_alibi_break",
        },
        {
            "id": "midnight",
            "summary": "the midnight gap",
            "requires_clues": ["butler_alibi_break"],
            "response": "Fine. I was in the cellar.",
        },
    ],
}


CLUES = [
    {"id": "butler_alibi_break", "title": "Butler alibi break",
     "source_path": "game/incident", "tags": []},
]


class TopicTests(unittest.TestCase):
    def test_unrequired_topic_always_available(self) -> None:
        t = Topic(id="x", summary="x", response="hi")
        self.assertTrue(t.is_available(set()))

    def test_required_clue_must_be_discovered(self) -> None:
        t = Topic(id="x", summary="x", response="hi", requires_clues=["c1"])
        self.assertFalse(t.is_available(set()))
        self.assertTrue(t.is_available({"c1"}))


class LoadDialogueTests(ScaffoldedCase):
    def _seed(self, *, dialogue: dict | None = None, slug: str = "butler") -> None:
        if dialogue is not None:
            d = self.target / "game" / "dialogue"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{slug}.json").write_text(json.dumps(dialogue), encoding="utf-8")

    def test_missing_directory_returns_empty(self) -> None:
        npcs, errors = load_dialogue(self.target)
        self.assertEqual(npcs, {})
        self.assertEqual(errors, [])

    def test_well_formed_file_loads(self) -> None:
        self._seed(dialogue=BUTLER)
        npcs, errors = load_dialogue(self.target)
        self.assertEqual(errors, [])
        self.assertIn("butler", npcs)
        butler = npcs["butler"]
        self.assertEqual(butler.name, "The Butler")
        self.assertEqual(len(butler.topics), 2)

    def test_invalid_json_reported(self) -> None:
        d = self.target / "game" / "dialogue"
        d.mkdir(parents=True, exist_ok=True)
        (d / "broken.json").write_text("{not", encoding="utf-8")
        _, errors = load_dialogue(self.target)
        self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_validate_surfaces_dialogue_errors(self) -> None:
        d = self.target / "game" / "dialogue"
        d.mkdir(parents=True, exist_ok=True)
        (d / "bad.json").write_text(
            json.dumps({"name": "X", "topics": [{"id": "a"}]}),
            encoding="utf-8",
        )
        errors = validate_project(self.target)
        self.assertTrue(any("dialogue" in e for e in errors))


class ShellAskTests(ScaffoldedCase):
    def setUp(self) -> None:
        super().setUp()
        d = self.target / "game" / "dialogue"
        d.mkdir(parents=True, exist_ok=True)
        (d / "butler.json").write_text(json.dumps(BUTLER), encoding="utf-8")
        (self.target / "game" / "clues.json").write_text(
            json.dumps(CLUES), encoding="utf-8"
        )

    def test_ask_with_no_args_lists_npcs(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask")
        self.assertIn("butler", buffer.getvalue())

    def test_ask_npc_lists_only_currently_available_topics(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask butler")
        out = buffer.getvalue()
        self.assertIn("chandelier", out)
        self.assertNotIn("midnight", out)  # gated on butler_alibi_break

    def test_ask_about_topic_reveals_clue(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask butler about chandelier")
        out = buffer.getvalue()
        self.assertIn("oiled it", out)
        self.assertIn("butler_alibi_break", shell.clue_registry.discovered)

    def test_gated_topic_blocks_until_required_clue(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask butler about midnight")
        self.assertIn("deflects", buffer.getvalue())

    def test_gated_topic_unlocks_after_dependency_revealed(self) -> None:
        shell = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell.onecmd("ask butler about chandelier")  # reveals dep
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask butler about midnight")
        self.assertIn("cellar", buffer.getvalue())

    def test_unknown_npc_message(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("ask ghost")
        self.assertIn("Unknown NPC", buffer.getvalue())

    def test_ask_emits_dialogue_event(self) -> None:
        shell = InvestigationShell(self.target)
        seen: list[dict] = []
        shell.events.subscribe("dialogue:asked", lambda p: seen.append(p))
        with redirect_stdout(io.StringIO()):
            shell.onecmd("ask butler about chandelier")
        self.assertEqual(seen, [{"npc": "butler", "topic": "chandelier"}])


if __name__ == "__main__":
    unittest.main()
