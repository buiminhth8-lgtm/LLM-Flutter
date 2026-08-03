from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.foreshadowing import ForeshadowingEvaluator


def test_foreshadowing_reads_registered_items():
    result = ForeshadowingEvaluator().evaluate(
        EvaluationInput(
            "chapter",
            "c1",
            "p1",
            "c1",
            "林烬进入黑市。",
            references={
                "world_entries": [
                    {"category": "foreshadowing", "title": "骨片印记", "content": "未来回收"}
                ]
            },
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["foreshadowing_unresolved_count"] == 1

