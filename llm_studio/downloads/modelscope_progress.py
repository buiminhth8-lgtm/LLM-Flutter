"""Bridge ModelScope SDK progress callbacks into LLM Studio job progress."""

from __future__ import annotations

import time
from collections.abc import Callable

from llm_studio.downloads.entities import DownloadProgress
from llm_studio.downloads.progress import DownloadProgressTracker, sanitize_remote_filename


class ModelScopeProgressBridge:
    def __init__(
        self,
        tracker: DownloadProgressTracker,
        flush: Callable[[DownloadProgress], None],
        *,
        throttle_seconds: float = 0.5,
    ):
        self.tracker = tracker
        self.flush = flush
        self.throttle_seconds = throttle_seconds
        self._last_flush = 0.0

    def callback_class(self):
        bridge = self

        class LlmStudioModelScopeProgressCallback:
            def __init__(self, filename: str, file_size: int):
                self.filename = sanitize_remote_filename(filename) or filename
                self.file_size = int(file_size) if file_size and file_size > 0 else None
                bridge._flush(
                    bridge.tracker.update_file(
                        self.filename,
                        downloaded_delta=0,
                        total_bytes=self.file_size,
                    ),
                    force=True,
                )

            def update(self, size: int) -> None:
                snapshot = bridge.tracker.update_file(
                    self.filename,
                    downloaded_delta=max(0, int(size or 0)),
                    total_bytes=self.file_size,
                )
                bridge._flush(snapshot)

            def end(self) -> None:
                bridge._flush(
                    bridge.tracker.finish_file(self.filename, total_bytes=self.file_size),
                    force=True,
                )

        return LlmStudioModelScopeProgressCallback

    def __call__(self, *args, **kwargs) -> None:
        filename = kwargs.get("filename") or kwargs.get("file") or kwargs.get("current_file")
        total_bytes = kwargs.get("file_size") or kwargs.get("total") or kwargs.get("total_bytes")
        downloaded = (
            kwargs.get("downloaded_bytes")
            or kwargs.get("downloaded")
            or kwargs.get("n")
            or kwargs.get("size")
            or 0
        )
        if args:
            if filename is None and isinstance(args[0], str):
                filename = args[0]
            elif isinstance(args[0], int):
                downloaded = args[0]
        snapshot = self.tracker.update_file(
            str(filename) if filename is not None else None,
            downloaded_delta=max(0, int(downloaded or 0)),
            total_bytes=int(total_bytes) if total_bytes else None,
        )
        self._flush(snapshot)

    def _flush(self, snapshot: DownloadProgress, *, force: bool = False) -> None:
        now = time.monotonic()
        if force or now - self._last_flush >= self.throttle_seconds:
            self._last_flush = now
            self.flush(snapshot)
