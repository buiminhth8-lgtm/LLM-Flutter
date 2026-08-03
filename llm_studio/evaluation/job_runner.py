"""JobQueue entry helpers for long Evaluation Center runs."""

from __future__ import annotations

import asyncio
from typing import Any


def run_evaluation_job(service: Any, run_id: str):
    def handler(job, update, cancel_flag) -> None:
        update(0.05, "Evaluation run started.")
        if cancel_flag.is_set():
            service.records.update_run(run_id, {"status": "cancelled"})
            return
        asyncio.run(service.start_run(run_id))
        update(1.0, "Evaluation run completed.")

    return handler

