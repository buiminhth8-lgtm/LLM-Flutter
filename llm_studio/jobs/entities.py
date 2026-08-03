"""Persistent background job entities."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from llm_studio.security.redaction import redact_sensitive_text


class JobType(str, Enum):
    MODEL_DOWNLOAD = "MODEL_DOWNLOAD"
    MODEL_SCAN = "MODEL_SCAN"
    MODEL_DELETE = "MODEL_DELETE"
    MODEL_VERIFY = "MODEL_VERIFY"
    BENCHMARK = "BENCHMARK"
    FINETUNE = "FINETUNE"
    LORA_MERGE = "LORA_MERGE"
    RAG_REBUILD = "RAG_REBUILD"
    CACHE_CLEANUP = "CACHE_CLEANUP"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


TERMINAL_JOB_STATUSES = {
    JobStatus.CANCELLED.value,
    JobStatus.SUCCEEDED.value,
    JobStatus.FAILED.value,
    JobStatus.INTERRUPTED.value,
}


@dataclass(frozen=True)
class Job:
    id: str
    type: str
    status: str
    progress: float | None
    message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    error_code: str | None
    error_message: str | None
    payload: dict[str, Any]

    @classmethod
    def new(cls, job_id: str, job_type: str, payload: dict[str, Any]) -> Job:
        return cls(
            id=job_id,
            type=job_type,
            status=JobStatus.PENDING.value,
            progress=None,
            message=None,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            finished_at=None,
            error_code=None,
            error_message=None,
            payload=payload,
        )

    def with_update(self, **changes: Any) -> Job:
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        def dt(value: datetime | None) -> str | None:
            return value.isoformat() if value else None

        return {
            "id": self.id,
            "type": self.type,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "created_at": dt(self.created_at),
            "started_at": dt(self.started_at),
            "finished_at": dt(self.finished_at),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "payload": self.payload,
        }

    def to_public_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data["error_message"] = redact_sensitive_text(self.error_message)
        data["payload"] = sanitize_job_payload(self.payload)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        def parse(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value) if value else None

        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            status=str(data["status"]),
            progress=float(data["progress"]) if data.get("progress") is not None else None,
            message=data.get("message"),
            created_at=parse(data.get("created_at")) or datetime.now(timezone.utc),
            started_at=parse(data.get("started_at")),
            finished_at=parse(data.get("finished_at")),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            payload=dict(data.get("payload") or {}),
        )


SENSITIVE_PAYLOAD_KEYS = {"token", "password", "api_key", "authorization", "cookie", "hf_token"}
SENSITIVE_PUBLIC_PAYLOAD_KEYS = {
    *SENSITIVE_PAYLOAD_KEYS,
    "secret",
    "file_path",
    "directory_path",
    "image_path",
    "local_path",
    "path",
}
SAFE_PUBLIC_PAYLOAD_KEYS = {"repo_id", "revision", "allow_patterns", "ignore_patterns", "model_id"}


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in SENSITIVE_PAYLOAD_KEYS:
            continue
        if isinstance(value, dict):
            cleaned[key] = sanitize_payload(value)
        else:
            cleaned[key] = value
    return cleaned


def sanitize_job_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        key_lower = key.lower()
        is_sensitive_key = key_lower in SENSITIVE_PUBLIC_PAYLOAD_KEYS or any(
            marker in key_lower
            for marker in ("token", "api_key", "authorization", "password", "secret", "path")
        )
        if key_lower not in SAFE_PUBLIC_PAYLOAD_KEYS and is_sensitive_key:
            cleaned[key] = "<redacted>"
        elif isinstance(value, dict):
            cleaned[key] = sanitize_job_payload(value)
        elif isinstance(value, list):
            cleaned[key] = [
                sanitize_job_payload(item) if isinstance(item, dict) else item for item in value
            ]
        elif isinstance(value, str):
            cleaned[key] = redact_sensitive_text(value)
        else:
            cleaned[key] = value
    return cleaned
