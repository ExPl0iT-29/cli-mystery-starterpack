"""Tests for the heuristic uniqueness solver."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.cli import main
from cli_mystery_starter.solver import analyze, slugify


def _people_with(*suspects: str) -> str:
    header = "NAME\tROLE\tAGE\tADDRESS\n"
    rows = "\n".join(f"{name}\tperson\t30\twherever" for name in suspects)
    return header + rows + "\n"


def _solutions(culprit: str, aliases: list[str] | None = None) -> dict:
    return {
        "answers": {
            "culprit": {
                "value": culprit,
                "aliases": list(aliases or []),
            }
        }
    }


class SlugifyTests(unittest.TestCase):
    def test_collapses_case_and_whitespace(self) -> None:
        self.assertEqual(slugify("Maria  Ortega"), "maria_ortega")
        self.assertEqual(slugify("  J.  Doe  "), "j._doe")


class SolverAnalyzeTests(ScaffoldedCase):
    def _seed(self, *, people: str, clues: list[dict], solutions: dict) -> None:
        (self.target / "game" / "people").write_text(people, encoding="utf-8")
        (self.target / "game" / "clues.json").write_text(
            json.dumps(clues), encoding="utf-8"
        )
        (self.target / "solutions.json").write_text(
            json.dumps(solutions), encoding="utf-8"
        )
        # Make sure clue source paths exist so the solver does not flag them.
        for c in clues:
            sp = self.target / c["source_path"]
            sp.parent.mkdir(parents=True, exist_ok=True)
            if not sp.exists():
                sp.write_text("placeholder\n", encoding="utf-8")

    def test_unique_solve(self) -> None:
        self._seed(
            people=_people_with("Maria Ortega", "Alex Mercer", "Leena Voss"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["points:maria_ortega"]},
                {"id": "b", "title": "y", "source_path": "game/logs/b.txt",
                 "tags": ["points:maria_ortega"]},
                {"id": "c", "title": "z", "source_path": "game/logs/c.txt",
                 "tags": ["exonerates:alex_mercer"]},
            ],
            solutions=_solutions("Maria Ortega", ["Ortega"]),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "UNIQUE")
        self.assertEqual(report.top_suspects, ["Maria Ortega"])
        self.assertEqual(report.scores["Maria Ortega"], 2)
        self.assertEqual(report.scores["Alex Mercer"], -1)

    def test_ambiguous_when_two_suspects_tie(self) -> None:
        self._seed(
            people=_people_with("Maria Ortega", "Alex Mercer"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["points:maria_ortega"]},
                {"id": "b", "title": "y", "source_path": "game/logs/b.txt",
                 "tags": ["points:alex_mercer"]},
            ],
            solutions=_solutions("Maria Ortega"),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "AMBIGUOUS")
        self.assertCountEqual(report.top_suspects,
                              ["Maria Ortega", "Alex Mercer"])

    def test_mismatch_when_top_scorer_is_not_canonical(self) -> None:
        self._seed(
            people=_people_with("Maria Ortega", "Alex Mercer"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["points:alex_mercer"]},
                {"id": "b", "title": "y", "source_path": "game/logs/b.txt",
                 "tags": ["points:alex_mercer"]},
                {"id": "c", "title": "z", "source_path": "game/logs/c.txt",
                 "tags": ["points:maria_ortega"]},
            ],
            solutions=_solutions("Maria Ortega"),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "MISMATCH")
        self.assertEqual(report.top_suspects, ["Alex Mercer"])

    def test_insufficient_when_no_clues(self) -> None:
        # No clues.json
        report = analyze(self.target)
        self.assertEqual(report.verdict, "INSUFFICIENT")

    def test_insufficient_when_no_directional_tags(self) -> None:
        self._seed(
            people=_people_with("Maria Ortega"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["timeline"]},
            ],
            solutions=_solutions("Maria Ortega"),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "INSUFFICIENT")

    def test_canonical_must_exist_in_people(self) -> None:
        self._seed(
            people=_people_with("Alex Mercer"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["points:alex_mercer"]},
            ],
            solutions=_solutions("Maria Ortega"),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "ERROR")
        self.assertTrue(any("not found" in e for e in report.errors))

    def test_aliases_can_match_canonical(self) -> None:
        self._seed(
            people=_people_with("M. Ortega"),
            clues=[
                {"id": "a", "title": "x", "source_path": "game/logs/a.txt",
                 "tags": ["points:m._ortega"]},
            ],
            solutions=_solutions("Maria Ortega", ["M. Ortega"]),
        )
        report = analyze(self.target)
        self.assertEqual(report.verdict, "UNIQUE")


class SolverCLITests(ScaffoldedCase):
    def test_check_solve_subcommand_dispatches(self) -> None:
        # Trivial seeded case
        (self.target / "game" / "people").write_text(
            _people_with("Maria Ortega"), encoding="utf-8"
        )
        (self.target / "game" / "clues.json").write_text(
            json.dumps([{
                "id": "a", "title": "x",
                "source_path": "game/incident",
                "tags": ["points:maria_ortega"],
            }]),
            encoding="utf-8",
        )
        (self.target / "solutions.json").write_text(
            json.dumps(_solutions("Maria Ortega")), encoding="utf-8"
        )
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = main(["check-solve", str(self.target)])
        self.assertEqual(rc, 0)
        self.assertIn("UNIQUE", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
