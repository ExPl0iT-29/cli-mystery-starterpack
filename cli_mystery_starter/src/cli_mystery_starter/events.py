"""In-process synchronous event bus.

Lightweight foundation for plugin-style extensions: subscribers register
handlers for named events; the shell emits events at well-known points.

Handler exceptions are caught and logged to stdout so a misbehaving
subscriber cannot crash the player's session. Events are intentionally
synchronous and ordered (subscribers fire in registration order) to keep
debugging simple.

Well-known event names emitted by `InvestigationShell`:

- `file:read`       payload: {"path": "<rel-posix-path>"}
- `suspect:marked`  payload: {"name": "<name>"}
- `note:added`      payload: {"text": "<note>", "index": <1-based>}
- `hint:read`       payload: {"number": <int>}
- `accuse:attempt`  payload: {"guess": "<name>", "correct": <bool>}
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler) -> None:
        self._subscribers[event].append(handler)

    def emit(self, event: str, payload: dict[str, Any] | None = None) -> None:
        data = dict(payload or {})
        for handler in list(self._subscribers.get(event, ())):
            try:
                handler(data)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[event:{event}] handler error: {exc}")

    def subscribers(self, event: str) -> list[Handler]:
        return list(self._subscribers.get(event, ()))
