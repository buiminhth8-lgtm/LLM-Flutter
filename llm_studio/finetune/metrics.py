"""Fine-tune metrics artifact writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FineTuneMetricsWriter:
    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "metrics.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        metric_type: str,
        *,
        step: int,
        epoch: float | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "type": metric_type,
            "step": int(step),
            **({"epoch": epoch} if epoch is not None else {}),
            **(metrics or {}),
        }
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
