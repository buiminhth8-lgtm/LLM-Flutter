"""Deterministic ranking helpers for memory retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .sources import source_weight


@dataclass(frozen=True)
class RankedChunk:
    chunk: dict[str, Any]
    score: float
    explain: dict[str, Any] = field(default_factory=dict)


_CJK = re.compile(r"[\u3400-\u9fff]")
_WORD = re.compile(r"[A-Za-z0-9_]+")


def extract_terms(text: str) -> list[str]:
    value = str(text or "").lower()
    terms = [item.group(0) for item in _WORD.finditer(value)]
    terms.extend(item.group(0) for item in _CJK.finditer(value))
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        if term and term not in seen:
            seen.add(term)
            result.append(term)
    return result


class MemoryRanker:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = {**{k: source_weight(k) for k in (
            "character",
            "world_entry",
            "plot_thread",
            "timeline_event",
            "chapter",
            "revision",
            "generation",
            "adapter_eval_result",
            "manual_note",
            "scene",
            "foreshadowing",
        )}, **(weights or {})}

    def rank(
        self,
        chunks: list[dict[str, Any]],
        *,
        query_text: str,
        chapter_id: str | None = None,
        scene_id: str | None = None,
    ) -> list[RankedChunk]:
        query_terms = extract_terms(query_text)
        ranked: list[RankedChunk] = []
        for chunk in chunks:
            document = chunk.get("document") or {}
            source_type = document.get("source_type") or chunk.get("source_type") or ""
            text = f"{document.get('title') or ''}\n{chunk.get('chunk_text') or ''}".lower()
            keyword_hits = sum(text.count(term) for term in query_terms if term)
            keyword_score = keyword_hits / max(1, len(query_terms))
            source_boost = float(self.weights.get(source_type, 1.0))
            priority = int(document.get("priority") or 0)
            user_priority_boost = min(0.5, max(0.0, priority / 20))
            direct_relation_boost = 0.0
            metadata = chunk.get("metadata") or {}
            if chapter_id and (
                document.get("source_id") == chapter_id
                or metadata.get("chapter_id") == chapter_id
            ):
                direct_relation_boost += 0.35
            if scene_id and (
                document.get("source_id") == scene_id
                or metadata.get("scene_id") == scene_id
            ):
                direct_relation_boost += 0.25
            recency_boost = 0.05 if document.get("updated_at") else 0.0
            score = keyword_score + source_boost + user_priority_boost + direct_relation_boost + recency_boost
            ranked.append(
                RankedChunk(
                    chunk=chunk,
                    score=round(score, 6),
                    explain={
                        "keyword_hits": keyword_hits,
                        "keyword_score": round(keyword_score, 6),
                        "source_weight": source_boost,
                        "priority_boost": round(user_priority_boost, 6),
                        "direct_relation_boost": round(direct_relation_boost, 6),
                        "recency_boost": recency_boost,
                    },
                )
            )
        return sorted(
            ranked,
            key=lambda item: (
                -item.score,
                -int((item.chunk.get("document") or {}).get("priority") or 0),
                str((item.chunk.get("document") or {}).get("updated_at") or ""),
                str((item.chunk.get("document") or {}).get("title") or ""),
                int(item.chunk.get("chunk_index") or 0),
            ),
        )

