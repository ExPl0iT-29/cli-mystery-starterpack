"""Tests for the answer verifier and the typed config schema."""

from __future__ import annotations

import unittest

from ._helpers import ScaffoldedCase

from cli_mystery_starter import verifier
from cli_mystery_starter.config import MysteryConfig


class VerifierTests(ScaffoldedCase):
    def test_fresh_scaffold_uses_sha256_salted_format(self) -> None:
        encoded = (self.target / "encoded").read_text(encoding="utf-8").strip()
        self.assertEqual(verifier.detect_format(encoded),
                         verifier.FORMAT_SHA256_SALTED)
        self.assertTrue(verifier.verify(encoded, "John Doe"))
        self.assertFalse(verifier.verify(encoded, "John Doer"))

    def test_verifier_normalizes_whitespace_on_sha256(self) -> None:
        encoded = verifier.hash_answer("Maria Ortega")
        self.assertTrue(verifier.verify(encoded, "  Maria   Ortega  "))
        # Case still matters
        self.assertFalse(verifier.verify(encoded, "maria ortega"))

    def test_verifier_supports_legacy_md5(self) -> None:
        legacy = verifier.hash_answer("Old Case", fmt=verifier.FORMAT_MD5_LEGACY)
        self.assertEqual(verifier.detect_format(legacy),
                         verifier.FORMAT_MD5_LEGACY)
        self.assertTrue(verifier.verify(legacy, "Old Case"))

    def test_unknown_format_returns_none(self) -> None:
        self.assertIsNone(verifier.detect_format("definitely-not-a-hash"))
        self.assertFalse(verifier.verify("definitely-not-a-hash", "anything"))


class ConfigTests(unittest.TestCase):
    def test_defaults_round_trip(self) -> None:
        cfg = MysteryConfig()
        as_dict = cfg.to_dict()
        rebuilt = MysteryConfig.from_dict(as_dict)
        self.assertEqual(rebuilt.to_dict(), as_dict)

    def test_rejects_unknown_keys(self) -> None:
        with self.assertRaises(ValueError):
            MysteryConfig.from_dict({"unknown_key": "x"})

    def test_rejects_unsafe_folders(self) -> None:
        with self.assertRaises(ValueError):
            MysteryConfig.from_dict({"folders": ["../escape"]})

    def test_rejects_invalid_hint_count(self) -> None:
        with self.assertRaises(ValueError):
            MysteryConfig.from_dict({"hint_count": 0})

    def test_rejects_unknown_answer_format(self) -> None:
        with self.assertRaises(ValueError):
            MysteryConfig.from_dict({"answer_format": "rot13"})

    def test_rejects_blank_clue_marker(self) -> None:
        with self.assertRaises(ValueError):
            MysteryConfig.from_dict({"clue_marker": "   "})


if __name__ == "__main__":
    unittest.main()
