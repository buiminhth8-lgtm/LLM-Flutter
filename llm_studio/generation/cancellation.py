"""Thread-safe generation cancellation token."""

from __future__ import annotations

from threading import Event


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    @property
    def event(self) -> Event:
        return self._event
