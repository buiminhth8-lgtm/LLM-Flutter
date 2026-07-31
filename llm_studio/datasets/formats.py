"""Dataset sample and export format definitions."""

from __future__ import annotations

DATASET_TYPES = frozenset({"sft", "preference", "mixed"})
DATASET_STATUSES = frozenset({"draft", "reviewing", "ready", "frozen", "dirty", "archived"})
SAMPLE_TYPES = frozenset({"sft", "preference"})
SAMPLE_STATUSES = frozenset({"pending", "approved", "rejected", "exported", "archived"})
DATASET_VERSION_STATUSES = frozenset({"frozen", "archived", "superseded"})
VERSION_SAMPLE_SPLITS = frozenset({"train", "val", "excluded"})
SPLIT_STRATEGIES = frozenset(
    {"group_by_project", "group_by_chapter", "random_by_sample", "no_validation"}
)
RECIPE_METHODS = frozenset({"lora", "qlora"})
RECIPE_STATUSES = frozenset({"draft", "confirmed", "archived"})
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
    if result not in SAMPLE_STATUSES:
        from .errors import DatasetInvalidStatusError

        raise DatasetInvalidStatusError(result)
    return result


def safe_dataset_version_status(value: str | None) -> str:
    result = str(value or "frozen").strip()
    if result not in DATASET_VERSION_STATUSES:
        from .errors import DatasetInvalidStatusError

        raise DatasetInvalidStatusError(result)
    return result


def safe_split_strategy(value: str | None) -> str:
    result = str(value or "group_by_chapter").strip()
    if result not in SPLIT_STRATEGIES:
        from .errors import DatasetSplitInvalidError

        raise DatasetSplitInvalidError(result)
    return result


def safe_version_sample_split(value: str | None) -> str:
    result = str(value or "train").strip()
    if result not in VERSION_SAMPLE_SPLITS:
        from .errors import DatasetSplitInvalidError

        raise DatasetSplitInvalidError(result)
    return result


def safe_recipe_method(value: str | None) -> str:
    result = str(value or "qlora").strip()
    if result not in RECIPE_METHODS:
        from .errors import DatasetRecipeInvalidMethodError

        raise DatasetRecipeInvalidMethodError(result)
    return result


def safe_recipe_status(value: str | None) -> str:
    result = str(value or "draft").strip()
    if result not in RECIPE_STATUSES:
        from .errors import DatasetInvalidStatusError

        raise DatasetInvalidStatusError(result)
    return result
