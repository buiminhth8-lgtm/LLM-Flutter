import time

import pytest

from llm_studio.generation import CancellationToken, GenerationCancelledError, GenerationTimeoutError, GenerationWorker
from llm_studio.generation.exceptions import GenerationError


class FakeStreamer:
    def __init__(self, chunks):
        self.chunks = iter(chunks)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.chunks)


def test_generation_worker_outputs_chunks():
    worker = GenerationWorker(target=lambda: None, streamer=FakeStreamer(["a", "b"]), timeout_seconds=1)
    assert list(worker) == ["a", "b"]


def test_generation_worker_propagates_exception():
    def boom():
        raise RuntimeError("bad")

    worker = GenerationWorker(target=boom, streamer=FakeStreamer([]), timeout_seconds=1)
    with pytest.raises(GenerationError):
        list(worker)


def test_generation_worker_timeout():
    def slow():
        time.sleep(0.2)

    class SlowStreamer:
        def __iter__(self):
            return self

        def __next__(self):
            time.sleep(0.2)
            return ""

    worker = GenerationWorker(target=slow, streamer=SlowStreamer(), timeout_seconds=0.01)
    with pytest.raises(GenerationTimeoutError):
        list(worker)


def test_generation_worker_cancelled():
    token = CancellationToken()
    token.cancel()
    worker = GenerationWorker(target=lambda: None, streamer=FakeStreamer(["x"]), cancellation_token=token)
    with pytest.raises(GenerationCancelledError):
        list(worker)
