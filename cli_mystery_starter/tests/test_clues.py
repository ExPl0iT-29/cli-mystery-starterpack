"""Tests for the optional clue object model."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.clues import Clue, ClueRegistry, load_clues
from cli_mystery_starter.events import EventBus
from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.validation import validate_project


SAMPLE_CLUES = [
    {
        "id": "ledger_44",
        "title": "Mismatched signature in the East Hall ledger",
        "source_path": "game/registry/ledger.txt",
        "tags": ["timeline", "alibi:butler"],
    },
    {
        "id": "interview_butler",
        "title": "Butler claims he was alone after midnight",
        "source_path": "game/interviews/butler.txt",
        "tags": ["alibi:butler"],
    },
]


class LoadCluesTests(ScaffoldedCase):
    def test_returns_empty_when_file_absent(self) -> None:
        clues, errors = load_clues(self.target)
        self.assertEqual(clues, [])
        self.assertEqual(errors, [])

    def test_parses_well_formed_file(self) -> None:
        (self.target / "game" / "clues.json").write_text(
            json.dumps(SAMPLE_CLUES), encoding="utf-8"
        )
        clues, errors = load_clues(self.target)
        self.assertEqual(errors, [])
        self.assertEqual([c.id for c in clues], ["ledger_44", "interview_butler"])
        self.assertEqual(clues[0].tags, ["timeline", "alibi:butler"])

    def test_reports_invalid_json(self) -> None:
        (self.target / "game" / "clues.json").write_text("{not json", encoding="utf-8")
        clues, errors = load_clues(self.target)
        self.assertEqual(clues, [])
        self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_reports_missing_fields(self) -> None:
        bad = [{"id": "x"}, {"id": "y", "title": "ok", "source_path": "p"}]
        (self.target / "game" / "clues.json").write_text(
            json.dumps(bad), encoding="utf-8"
        )
        _, errors = load_clues(self.target)
        self.assertTrue(errors)

    def test_validate_surfaces_clue_errors(self) -> None:
        (self.target / "game" / "clues.json").write_text("not a list", encoding="utf-8")
        errors = validate_project(self.target)
        self.assertTrue(any("clues.json" in e for e in errors))


class ClueRegistryTests(ScaffoldedCase):
    def _registry(self) -> tuple[EventBus, ClueRegistry]:
        clues = [Clue(**item) for item in SAMPLE_CLUES]
        bus = EventBus()
        registry = ClueRegistry(clues)
        registry.attach(bus)
        return bus, registry

    def test_file_read_event_marks_matching_clue(self) -> None:
        bus, registry = self._registry()
        bus.emit("file:read", {"path": "game/registry/ledger.txt"})
        self.assertEqual(
            {c.id for c in registry.discovered_clues()},
            {"ledger_44"},
        )

    def test_unrelated_path_does_not_discover(self) -> None:
        bus, registry = self._registry()
        bus.emit("file:read", {"path": "game/incident"})
        self.assertEqual(registry.discovered_clues(), [])

    def test_attach_seeds_initial_discovered(self) -> None:
        clues = [Clue(**item) for item in SAMPLE_CLUES]
        registry = ClueRegistry(clues)
        registry.attach(EventBus(), initial=["ledger_44", "ghost_id_not_in_set"])
        # Only known IDs survive
        self.assertEqual(registry.discovered, {"ledger_44"})


class ShellCluesIntegrationTests(ScaffoldedCase):
    def setUp(self) -> None:
        super().setUp()
        # Plant a clue with a real source file so cat triggers discovery
        (self.target / "game" / "logs").mkdir(exist_ok=True)
        (self.target / "game" / "logs" / "alarm.txt").write_text(
            "Alarm tripped 02:14\n", encoding="utf-8"
        )
        (self.target / "game" / "clues.json").write_text(
            json.dumps([{
                "id": "alarm_at_2_14",
                "title": "Alarm tripped at 2:14am",
                "source_path": "game/logs/alarm.txt",
                "tags": ["timeline"],
            }]),
            encoding="utf-8",
        )

    def test_cat_discovers_clue_and_clues_verb_lists_it(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("cat /game/logs/alarm.txt")
            shell.onecmd("clues")
        output = buffer.getvalue()
        self.assertIn("Discovered 1 / 1 clues", output)
        self.assertIn("alarm_at_2_14", output)

    def test_discovered_clues_persist_across_runs(self) -> None:
        shell1 = InvestigationShell(self.target)
        with redirect_stdout(io.StringIO()):
            shell1.onecmd("cat /game/logs/alarm.txt")
            shell1.onecmd("quit")
        shell2 = InvestigationShell(self.target)
        self.assertIn("alarm_at_2_14", shell2.clue_registry.discovered)


if __name__ == "__main__":
    unittest.main()
