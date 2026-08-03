from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.style_consistency import StyleConsistencyEvaluator


def test_style_consistency_outputs_style_score():
    result = StyleConsistencyEvaluator().evaluate(
        EvaluationInput(
            "chapter",
            "c1",
            "p1",
            "c1",
            "我走进黑市。我听见风声。我没有回头。他停在门口。他看见灯火。他没有说话。",
            references={"project": {"target_style": "紧张 压迫"}},
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert "style_score" in metrics
    assert metrics["pov_shift_count"] >= 1
