from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.pacing import PacingEvaluator


def test_pacing_outputs_dialogue_ratio_and_long_paragraph_count():
    text = "他说：“走。”\n" + "夜色" * 160
    result = PacingEvaluator().evaluate(EvaluationInput("chapter", "c1", "p1", "c1", text))
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert "dialogue_ratio" in metrics
    assert metrics["long_paragraph_count"] >= 1

