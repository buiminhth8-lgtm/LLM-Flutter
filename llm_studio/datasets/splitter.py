"""Train / validation split strategies for frozen dataset versions."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from llm_studio.api import errors as api_errors

from .formats import safe_split_strategy


class DatasetSplitter:
    def split(
        self,
        entries: list[dict[str, Any]],
        *,
        strategy: str = "group_by_chapter",
        val_ratio: float = 0.1,
        seed: int = 42,
    ) -> dict[str, Any]:
        strategy = safe_split_strategy(strategy)
        val_ratio = max(0.0, min(float(val_ratio), 0.5))
        warnings: list[dict[str, Any]] = []
        if strategy == "no_validation" or len(entries) < 10 or val_ratio <= 0:
            if len(entries) < 10:
                warnings.append(
                    {
                        "code": "DATASET_SMALL_VALIDATION_SET",
                        "message": "样本数量过少，验证集可能不稳定，本次不生成验证集。",
                    }
                )
            warnings.append(
                {
                    "code": api_errors.DATASET_NO_VALIDATION_SPLIT,
                    "message": "本次冻结未生成 validation split。",
                }
            )
            return {"train": list(entries), "val": [], "warnings": warnings}

        groups = self._groups(entries, strategy)
        shuffled = list(groups.items())
        random.Random(seed).shuffle(shuffled)
        target_val = max(1, round(len(entries) * val_ratio))
        val_group_keys: set[str] = set()
        val_count = 0
        for key, group_entries in shuffled:
            if len(val_group_keys) >= len(shuffled) - 1:
                break
            val_group_keys.add(key)
            val_count += len(group_entries)
            if val_count >= target_val:
                break
        train: list[dict[str, Any]] = []
        val: list[dict[str, Any]] = []
        for key, group_entries in groups.items():
            if key in val_group_keys:
                val.extend(group_entries)
            else:
                train.extend(group_entries)
        if not val:
            warnings.append(
                {
                    "code": api_errors.DATASET_NO_VALIDATION_SPLIT,
                    "message": "分组后验证集为空，建议补充更多章节样本。",
                }
            )
        return {"train": train, "val": val, "warnings": warnings}

    @staticmethod
    def _groups(entries: list[dict[str, Any]], strategy: str) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entry in entries:
            sample = entry["sample"]
            if strategy == "group_by_project":
                key = sample.get("project_id") or sample.get("sample_id")
            elif strategy == "random_by_sample":
                key = sample.get("sample_id")
            else:
                key = (
                    sample.get("chapter_id")
                    or sample.get("revision_id")
                    or sample.get("sample_id")
                )
            groups[str(key)].append(entry)
        return dict(groups)
