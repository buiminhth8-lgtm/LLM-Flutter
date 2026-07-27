"""Local model repository entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class StrEnum(str, Enum):
    """Python 3.10 compatible string enum."""

    def __str__(self) -> str:
        return self.value


class ModelFormat(StrEnum):
    TRANSFORMERS = "transformers"
    GGUF = "gguf"
    GPTQ = "gptq"
    AWQ = "awq"
    UNKNOWN = "unknown"


class ModelStatus(StrEnum):
    READY = "ready"
    INCOMPLETE = "incomplete"
    CORRUPTED = "corrupted"
    DOWNLOADING = "downloading"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class LocalModel:
    id: str
    display_name: str
    path: Path
    format: ModelFormat
    status: ModelStatus
    architecture: str | None
    parameter_count: int | None
    quantization: str | None
    context_length: int | None
    size_bytes: int
    files: tuple[str, ...]
    source_repo: str | None = None
    revision: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata_errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        resolved = self.path.expanduser().resolve()
        object.__setattr__(self, "path", resolved)
        if not self.id or any(sep in self.id for sep in ("/", "\\", ":", "..")):
            raise ValueError("模型 ID 必须是安全的仓库内部标识，不能直接使用用户路径。")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "path": str(self.path),
            "format": self.format.value,
            "status": self.status.value,
            "architecture": self.architecture,
            "parameter_count": self.parameter_count,
            "quantization": self.quantization,
            "context_length": self.context_length,
            "size_bytes": self.size_bytes,
            "files": list(self.files),
            "source_repo": self.source_repo,
            "revision": self.revision,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata_errors": list(self.metadata_errors),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> LocalModel:
        def parse_dt(value: object) -> datetime | None:
            if not value:
                return None
            return datetime.fromisoformat(str(value))

        return cls(
            id=str(data["id"]),
            display_name=str(data["display_name"]),
            path=Path(str(data["path"])),
            format=ModelFormat(str(data.get("format", ModelFormat.UNKNOWN.value))),
            status=ModelStatus(str(data.get("status", ModelStatus.READY.value))),
            architecture=data.get("architecture") if data.get("architecture") else None,
            parameter_count=int(data["parameter_count"]) if data.get("parameter_count") else None,
            quantization=data.get("quantization") if data.get("quantization") else None,
            context_length=int(data["context_length"]) if data.get("context_length") else None,
            size_bytes=int(data.get("size_bytes", 0)),
            files=tuple(str(item) for item in data.get("files", [])),
            source_repo=data.get("source_repo") if data.get("source_repo") else None,
            revision=data.get("revision") if data.get("revision") else None,
            created_at=parse_dt(data.get("created_at")),
            updated_at=parse_dt(data.get("updated_at")),
            metadata_errors=tuple(str(item) for item in data.get("metadata_errors", [])),
        )
