"""Cancellable streaming generation worker."""

from __future__ import annotations

import time
from queue import Empty, Queue
from threading import Thread
from typing import Callable, Iterator

from .cancellation import CancellationToken
from .exceptions import (
    GenerationCancelledError,
    GenerationTimeoutError,
    map_generation_exception,
)


class GenerationWorker:
    """Run a blocking model.generate call behind a TextIteratorStreamer."""

    def __init__(
        self,
        *,
        target: Callable[[], None],
        streamer,
        cancellation_token: CancellationToken | None = None,
        timeout_seconds: float = 300,
        join_timeout_seconds: float = 5,
    ) -> None:
        self.target = target
        self.streamer = streamer
        self.cancellation_token = cancellation_token or CancellationToken()
        self.timeout_seconds = timeout_seconds
        self.join_timeout_seconds = join_timeout_seconds
        self._errors: Queue[BaseException] = Queue(maxsize=1)
        self._thread = Thread(target=self._run, name="llm-studio-generation", daemon=True)

    def __iter__(self) -> Iterator[str]:
        started_at = time.monotonic()
        self._thread.start()
        try:
            while self._thread.is_alive():
                if self.cancellation_token.is_cancelled:
                    raise GenerationCancelledError("生成已取消。")
                if self.timeout_seconds > 0 and time.monotonic() - started_at > self.timeout_seconds:
                    self.cancellation_token.cancel()
                    raise GenerationTimeoutError(f"生成超时，超过 {self.timeout_seconds:.0f} 秒。")
                self._raise_worker_error_if_any()
                try:
                    chunk = next(self.streamer)
                    if chunk:
                        yield chunk
                except StopIteration:
                    break
                except Empty:
                    continue
            self._raise_worker_error_if_any()
            for chunk in self.streamer:
                if self.cancellation_token.is_cancelled:
                    raise GenerationCancelledError("生成已取消。")
                if chunk:
                    yield chunk
            self._raise_worker_error_if_any()
        except GeneratorExit:
            self.cancellation_token.cancel()
            raise
        finally:
            self.cancellation_token.cancel()
            self._thread.join(timeout=self.join_timeout_seconds)

    def _run(self) -> None:
        try:
            if not self.cancellation_token.is_cancelled:
                self.target()
        except BaseException as exc:
            try:
                self._errors.put_nowait(exc)
            except Exception:
                pass

    def _raise_worker_error_if_any(self) -> None:
        if self._errors.qsize():
            raise map_generation_exception(self._errors.get_nowait())
