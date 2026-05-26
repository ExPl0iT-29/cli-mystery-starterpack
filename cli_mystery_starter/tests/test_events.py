"""Tests for EventBus and the events the shell emits."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from ._helpers import ScaffoldedCase

from cli_mystery_starter.events import EventBus
from cli_mystery_starter.runtime import InvestigationShell


class EventBusTests(unittest.TestCase):
    def test_subscribe_and_emit_in_order(self) -> None:
        bus = EventBus()
        seen: list[tuple[str, str]] = []
        bus.subscribe("ping", lambda d: seen.append(("a", d["v"])))
        bus.subscribe("ping", lambda d: seen.append(("b", d["v"])))
        bus.emit("ping", {"v": "1"})
        self.assertEqual(seen, [("a", "1"), ("b", "1")])

    def test_emit_with_no_subscribers_is_a_noop(self) -> None:
        bus = EventBus()
        bus.emit("nobody:listening", {"x": 1})  # must not raise

    def test_handler_exception_does_not_break_other_handlers(self) -> None:
        bus = EventBus()
        seen: list[str] = []

        def boom(_):
            raise RuntimeError("boom")

        bus.subscribe("e", boom)
        bus.subscribe("e", lambda _: seen.append("ok"))
        with redirect_stdout(io.StringIO()):
            bus.emit("e", {})
        self.assertEqual(seen, ["ok"])


class ShellEventsTests(ScaffoldedCase):
    def test_shell_emits_documented_events(self) -> None:
        shell = InvestigationShell(self.target)
        seen: list[tuple[str, dict]] = []

        for name in ("file:read", "suspect:marked", "note:added",
                     "hint:read", "accuse:attempt"):
            shell.events.subscribe(
                name,
                lambda payload, n=name: seen.append((n, payload)),
            )

        with redirect_stdout(io.StringIO()):
            shell.onecmd("cat incident")
            shell.onecmd("mark Maria")
            shell.onecmd("note follow up on the chandelier")
            shell.onecmd("hint 1")
            shell.onecmd("accuse John Doe")

        names = [n for n, _ in seen]
        self.assertIn("file:read", names)
        self.assertIn("suspect:marked", names)
        self.assertIn("note:added", names)
        self.assertIn("hint:read", names)
        self.assertIn("accuse:attempt", names)

        # Validate payload shape on a couple of events
        accuse = next(p for n, p in seen if n == "accuse:attempt")
        self.assertEqual(accuse["guess"], "John Doe")
        self.assertTrue(accuse["correct"])

        file_read = next(p for n, p in seen if n == "file:read")
        self.assertEqual(file_read["path"], "game/incident")


if __name__ == "__main__":
    unittest.main()
