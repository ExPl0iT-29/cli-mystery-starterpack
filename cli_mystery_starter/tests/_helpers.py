"""Shared test scaffolding: sys.path insert + project factory."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from cli_mystery_starter import verifier  # noqa: E402
from cli_mystery_starter.scaffold import DEFAULT_CONFIG, create_project  # noqa: E402


def set_real_answer(target: Path, answer: str = "Maria Ortega") -> None:
    """Overwrite the placeholder `encoded` so `validate` passes."""
    encoded = verifier.hash_answer(answer)
    (target / "encoded").write_text(encoded + "\n", encoding="utf-8")


class ScaffoldedCase(unittest.TestCase):
    """Base TestCase that produces a fresh scaffold at `self.target`."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.target = self.root / "case"
        create_project(self.target, dict(DEFAULT_CONFIG))

    def tearDown(self) -> None:
        self._tmp.cleanup()
