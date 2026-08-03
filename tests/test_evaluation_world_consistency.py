from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.world_consistency import WorldConsistencyEvaluator


def test_world_consistency_detects_rule_conflict():
    result = WorldConsistencyEvaluator().evaluate(
        EvaluationInput(
            "chapter",
            "c1",
            "p1",
            "c1",
            "林烬在黑市使用灵火照亮墙壁。",
            references={"world_entries": [{"title": "黑市规则", "content": "黑市禁止灵火"}]},
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["world_conflict_count"] >= 1
    assert any(item.category == "world" for item in result.findings)

