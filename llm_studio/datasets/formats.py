"""Dataset sample and export format definitions."""

from __future__ import annotations

DATASET_TYPES = frozenset({"sft", "preference", "mixed"})
DATASET_STATUSES = frozenset({"draft", "reviewing", "ready", "archived"})
SAMPLE_TYPES = frozenset({"sft", "preference"})
SAMPLE_STATUSES = frozenset({"pending", "approved", "rejected", "exported", "archived"})
EXPORT_FORMATS = frozenset(
    {"sft_jsonl", "alpaca_jsonl", "chatml_jsonl", "preference_jsonl"}
)

DEFAULT_SFT_INSTRUCTION = "根据以下小说设定、人物、世界观和章节目标，创作或改写小说正文。"
CHATML_SYSTEM_PROMPT = "你是一名专业小说作者。"


def safe_export_format(value: str | None) -> str:
    result = str(value or "sft_jsonl").strip()
    if result not in EXPORT_FORMATS:
        from .errors import DatasetInvalidExportFormatError

        raise DatasetInvalidExportFormatError(result)
    return result


def safe_dataset_type(value: str | None) -> str:
    result = str(value or "sft").strip()
    if result not in DATASET_TYPES:
        from .errors import DatasetInvalidTypeError

        raise DatasetInvalidTypeError(result)
    return result


def safe_dataset_status(value: str | None) -> str:
    result = str(value or "draft").strip()
    if result == "frozen":
        from .errors import DatasetVersionNotImplementedError

        raise DatasetVersionNotImplementedError()
    if result not in DATASET_STATUSES:
        from .errors import DatasetInvalidStatusError

        raise DatasetInvalidStatusError(result)
    return result


def safe_sample_type(value: str | None) -> str:
    result = str(value or "sft").strip()
    if result not in SAMPLE_TYPES:
        from .errors import DatasetInvalidSampleTypeError

        raise DatasetInvalidSampleTypeError(result)
    return result


def safe_sample_status(value: str | None) -> str:
    result = str(value or "pending").strip()
    if result == "frozen":
        from .errors import DatasetVersionNotImplementedError

        raise DatasetVersionNotImplementedError()
    if result not in SAMPLE_STATUSES:
        from .errors import DatasetInvalidStatusError

        raise DatasetInvalidStatusError(result)
    return result
