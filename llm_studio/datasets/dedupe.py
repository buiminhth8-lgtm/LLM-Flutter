"""Hash and near-duplicate checks for dataset freezing."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from llm_studio.api import errors as api_errors

_PUNCT_OR_SPACE_RE = re.compile(r"[\s，。！？、；：,.!?;:'\"“”‘’（）()《》<>【】\[\]—…·\-]+")


def normalized_text(sample: dict[str, Any]) -> str:
    text = "\n".join(
        str(sample.get(field) or "")
        for field in ("instruction", "input", "output", "chosen", "rejected")
    ).lower()
    return _PUNCT_OR_SPACE_RE.sub("", text)


class DatasetDedupeService:
    def dedupe(
        self,
        samples: list[dict[str, Any]],
        *,
        exact_hash: bool = True,
        near_duplicate: bool = True,
        near_duplicate_threshold: float = 0.92,
    ) -> dict[str, Any]:
        kept: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        seen_hashes: dict[str, dict[str, Any]] = {}
        for sample in samples:
            content_hash = sample.get("content_hash") or ""
            entry = {
                "sample": sample,
                "warnings": list(sample.get("warnings") or []),
                "duplicate_group_id": None,
                "content_hash": content_hash,
            }
            if exact_hash and content_hash in seen_hashes:
                first = seen_hashes[content_hash]["sample"]
                entry["duplicate_group_id"] = f"exact-{content_hash[:12]}"
                entry["warnings"].append(
                    {
                        "code": api_errors.DATASET_EXACT_DUPLICATE,
                        "message": "样本 content_hash 与另一条样本完全重复，已排除。",
                        "similar_sample_id": first.get("sample_id"),
                    }
                )
                excluded.append(entry)
                continue
            if exact_hash:
                seen_hashes[content_hash] = entry
            kept.append(entry)
        if near_duplicate:
            self._mark_near_duplicates(
                kept,
                threshold=max(0.0, min(float(near_duplicate_threshold), 1.0)),
            )
        warning_count = sum(len(entry["warnings"]) for entry in [*kept, *excluded])
        return {
            "kept": kept,
            "excluded": excluded,
            "rejected_duplicate_count": len(excluded),
            "warning_count": warning_count,
        }

    def _mark_near_duplicates(self, entries: list[dict[str, Any]], *, threshold: float) -> None:
        buckets: dict[int, list[tuple[dict[str, Any], str]]] = {}
        for entry in entries:
            norm = normalized_text(entry["sample"])
            if not norm:
                continue
            bucket = len(norm) // 100
            for nearby in (bucket - 1, bucket, bucket + 1):
                for other_entry, other_norm in buckets.get(nearby, []):
                    if not other_norm:
                        continue
                    shorter = min(len(norm), len(other_norm))
                    longer = max(len(norm), len(other_norm))
                    if longer and shorter / longer < 0.75:
                        continue
                    similarity = SequenceMatcher(None, norm, other_norm, autojunk=False).ratio()
                    if similarity >= threshold:
                        entry["warnings"].append(
                            {
                                "code": api_errors.DATASET_NEAR_DUPLICATE,
                                "message": "样本与另一条样本相似度过高。",
                                "similar_sample_id": other_entry["sample"].get("sample_id"),
                                "similarity": round(similarity, 4),
                            }
                        )
                        break
                if entry["warnings"] and entry["warnings"][-1]["code"] == api_errors.DATASET_NEAR_DUPLICATE:
                    break
            buckets.setdefault(bucket, []).append((entry, norm))
