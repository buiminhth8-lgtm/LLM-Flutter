"""DatasetVersion immutable content hashing helpers."""

from __future__ import annotations

import hashlib
from typing import Any


def build_dataset_version_hash(
    *,
    train_hash: str,
    val_hash: str | None,
    version_samples: list[dict[str, Any]],
    split: dict[str, Any],
    export_format: str,
) -> str:
    parts = [export_format, train_hash, val_hash or "", repr(sorted(split.items()))]
    for item in sorted(version_samples, key=lambda row: (row["split"], row["sample_order"], row["sample_id"])):
        parts.extend(
            [
                item["split"],
                str(item["sample_order"]),
                item["sample_id"],
                item["content_hash"],
            ]
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
