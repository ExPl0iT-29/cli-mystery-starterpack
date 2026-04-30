"""Tests for the optional multi-field, multi-ending solution model."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.runtime import InvestigationShell
from cli_mystery_starter.solutions import (
    FieldSpec,
    load_solutions,
    parse_accusation,
)
from cli_mystery_starter.validation import validate_project


SAMPLE = {
    "answers": {
        "culprit": {"value": "Maria Ortega", "aliases": ["Ortega", "M. Ortega"]},
        "motive":  {"value": "inheritance"},
        "weapon":  {"value": "chandelier"},
    },
    "endings": [
        {"id": "full_solve",
         "requires": ["culprit", "motive", "weapon"],
         "text": "You proved every piece of the case."},
        {"id": "partial",
         "requires": ["culprit"],
         "text": "Right person, wrong story."},
    ],
}


class FieldSpecTests(unittest.TestCase):
    def test_value_match_is_case_and_whitespace_insensitive(self) -> None:
        spec = FieldSpec(value="Maria Ortega", aliases=[])
        self.assertTrue(spec.matches("maria ortega"))
        self.assertTrue(spec.matches("  Maria   Ortega  "))
        self.assertFalse(spec.matches("Maria Ortez"))

    def test_aliases_match(self) -> None:
        spec = FieldSpec(value="Maria Ortega", aliases=["Ortega"])
        self.assertTrue(spec.matches("ortega"))


class ParseAccusationTests(unittest.TestCase):
    def test_bare_name_becomes_culprit(self) -> None:
        self.assertEqual(parse_accusation("Maria Ortega"),
                         {"culprit": "Maria Ortega"})

    def test_keyed_form(self) -> None:
        self.assertEqual(
            parse_accusation('culprit="Maria Ortega" motive=inheritance'),
            {"culprit": "Maria Ortega", "motive": "inheritance"},
        )

    def test_empty_returns_empty_map(self) -> None:
        self.assertEqual(parse_accusation(""), {})


class LoadSolutionsTests(ScaffoldedCase):
    def test_absent_file_returns_none_no_errors(self) -> None:
        sol, errors = load_solutions(self.target)
        self.assertIsNone(sol)
        self.assertEqual(errors, [])

    def test_well_formed_file_loads(self) -> None:
        (self.target / "solutions.json").write_text(
            json.dumps(SAMPLE), encoding="utf-8"
        )
        sol, errors = load_solutions(self.target)
        self.assertEqual(errors, [])
        assert sol is not None
        self.assertIn("culprit", sol.fields)
        self.assertEqual([e.id for e in sol.endings], ["full_solve", "partial"])

    def test_invalid_json_reported(self) -> None:
        (self.target / "solutions.json").write_text("{not", encoding="utf-8")
        sol, errors = load_solutions(self.target)
        self.assertIsNone(sol)
        self.assertTrue(any("invalid JSON" in e for e in errors))

    def test_unknown_required_field_reported(self) -> None:
        bad = {
            "answers": {"culprit": {"value": "X"}},
            "endings": [{"id": "e", "requires": ["mystery_meat"], "text": ""}],
        }
        (self.target / "solutions.json").write_text(
            json.dumps(bad), encoding="utf-8"
        )
        sol, errors = load_solutions(self.target)
        self.assertIsNone(sol)
        self.assertTrue(any("unknown field" in e for e in errors))

    def test_validate_surfaces_solution_errors(self) -> None:
        (self.target / "solutions.json").write_text(
            json.dumps({"answers": "not-an-object"}), encoding="utf-8"
        )
        errors = validate_project(self.target)
        self.assertTrue(any("solutions.json" in e for e in errors))

    def test_default_ending_synthesized_when_endings_omitted(self) -> None:
        no_endings = {"answers": {"culprit": {"value": "X"}}}
        (self.target / "solutions.json").write_text(
            json.dumps(no_endings), encoding="utf-8"
        )
        sol, errors = load_solutions(self.target)
        self.assertEqual(errors, [])
        assert sol is not None
        self.assertEqual([e.id for e in sol.endings], ["solve"])
        self.assertEqual(sol.endings[0].requires, ["culprit"])


class SolutionsRuntimeTests(ScaffoldedCase):
    def setUp(self) -> None:
        super().setUp()
        (self.target / "solutions.json").write_text(
            json.dumps(SAMPLE), encoding="utf-8"
        )

    def test_full_solve_picks_full_ending(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd(
                'accuse culprit="Maria Ortega" motive=inheritance weapon=chandelier'
            )
        output = buffer.getvalue()
        self.assertIn("proved every piece", output)
        self.assertIn("full_solve", output)

    def test_culprit_only_picks_partial_ending(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("accuse Maria Ortega")
        output = buffer.getvalue()
        self.assertIn("Right person", output)
        self.assertIn("partial", output)

    def test_alias_resolves_to_culprit(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("accuse Ortega")
        self.assertIn("partial", buffer.getvalue())

    def test_no_match_reports_what_was_correct(self) -> None:
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd(
                'accuse culprit="Wrong Name" motive=inheritance'
            )
        output = buffer.getvalue()
        self.assertIn("does not unlock any ending", output)
        self.assertIn("motive", output)  # field correctly identified


class LegacyFallbackTests(ScaffoldedCase):
    def test_legacy_encoded_path_still_works_when_no_solutions_json(self) -> None:
        # No solutions.json at all
        shell = InvestigationShell(self.target)
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            shell.onecmd("accuse John Doe")
        self.assertIn("Accusation accepted", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
