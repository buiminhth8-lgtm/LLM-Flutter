from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.memory_usage import MemoryUsageEvaluator


def test_memory_usage_reads_retrieval_record_shape():
    retrieval = {
        "query_text": "黑市 灵骨",
        "selected_chunks": [
            {"chunk_id": "m1", "title": "黑市", "text": "黑市里有灵骨交易。"},
            {"chunk_id": "m2", "title": "海边", "text": "海风吹过码头。"},
        ],
    }
    result = MemoryUsageEvaluator().evaluate(
        EvaluationInput(
            "generation",
            "g1",
            "p1",
            "c1",
            "林烬在黑市发现灵骨交易。",
            references={"memory_retrieval": retrieval},
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["memory_usage_score"] >= 1
    assert metrics["irrelevant_memory_count"] >= 1

