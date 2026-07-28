"""LoRA adapter entities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AdapterInfo:
    id: str
    name: str
    path: Path
    base_model_name_or_path: str | None
    peft_type: str | None
    task_type: str | None
    rank: int | None
    alpha: float | None
    target_modules: tuple[str, ...]
    size_bytes: int
    compatible: bool
    compatibility_errors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", self.path.expanduser().resolve())

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "base_model_name_or_path": self.base_model_name_or_path,
            "peft_type": self.peft_type,
            "task_type": self.task_type,
            "rank": self.rank,
            "alpha": self.alpha,
            "target_modules": list(self.target_modules),
            "size_bytes": self.size_bytes,
            "compatible": self.compatible,
            "compatibility_errors": list(self.compatibility_errors),
        }
