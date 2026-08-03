"""Memory / RAG usage heuristics."""

from __future__ import annotations

from .base import EvaluationFindingDraft, EvaluationInput, EvaluationMetricDraft, EvaluationResult
from .plot_coherence import _terms


def _chunk_text(chunk: dict) -> str:
    return str(chunk.get("text") or chunk.get("chunk_text") or chunk.get("title") or "")


class MemoryUsageEvaluator:
    evaluator_type = "memory_usage"

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        retrieval = input.references.get("memory_retrieval") or {}
        chunks = list(retrieval.get("selected_chunks") or retrieval.get("retrieved_chunks") or [])
        query = str(retrieval.get("query_text") or input.context.get("current_chapter_goal") or "")
        query_terms = _terms(query)
        text_terms = _terms(input.text)
        chunk_relevance_scores: list[float] = []
        unused = []
        irrelevant = []
        for chunk in chunks:
            ctext = _chunk_text(chunk)
            cterms = _terms(ctext)
            relevance = len(query_terms & cterms) / max(1, len(query_terms)) if query_terms else 0.0
            used = bool(cterms & text_terms)
            chunk_relevance_scores.append(relevance)
            if not used:
                unused.append({"chunk_id": chunk.get("chunk_id"), "title": chunk.get("title"), "text": ctext[:120]})
            if relevance < 0.1 and query_terms:
                irrelevant.append({"chunk_id": chunk.get("chunk_id"), "title": chunk.get("title"), "text": ctext[:120]})
        relevance = sum(chunk_relevance_scores) / max(1, len(chunk_relevance_scores)) if chunks else 0.0
        missing_key = 0
        for term in query_terms:
            if term not in text_terms and len(term) >= 2:
                missing_key += 1
        score = 1.0 + relevance * 2.0 + max(0.0, 1.0 - len(unused) / max(1, len(chunks))) * 2.0
        findings: list[EvaluationFindingDraft] = []
        if unused:
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "memory",
                    "部分召回记忆未被正文明显使用",
                    "检索结果与正文缺少关键词交集，可能是未使用或表达被改写。",
                    {"unused_memory": unused[:10]},
                    "人工判断是否需要使用这些记忆，或降低召回权重。",
                )
            )
        if irrelevant:
            findings.append(
                EvaluationFindingDraft(
                    "warning",
                    "memory",
                    "疑似召回无关记忆",
                    "部分 retrieved_memory 与 query_text 关键词重合很低。",
                    {"irrelevant_memory": irrelevant[:10], "query": query},
                    "检查 Memory source filter、top_k 和关键词索引。",
                )
            )
        if not chunks and input.target_type != "memory_retrieval":
            findings.append(
                EvaluationFindingDraft(
                    "info",
                    "memory",
                    "没有可用 Memory 检索记录",
                    "本次目标没有关联 memory_retrieval_records，Memory 使用评估仅输出空结果。",
                    {},
                    "如果需要评估 RAG 召回，请先启用 memory.enabled 并保留 retrieval_id。",
                )
            )
        return EvaluationResult(
            metrics=[
                EvaluationMetricDraft("memory_recall_relevance", round(relevance, 4), "ratio"),
                EvaluationMetricDraft("memory_usage_score", round(max(1.0, min(5.0, score)), 2), "score"),
                EvaluationMetricDraft("unused_memory_count", float(len(unused)), "count"),
                EvaluationMetricDraft("missing_key_memory_count", float(missing_key), "count"),
                EvaluationMetricDraft("irrelevant_memory_count", float(len(irrelevant)), "count"),
            ],
            findings=findings,
            summary="Memory / RAG 使用启发式评估完成。",
        )

