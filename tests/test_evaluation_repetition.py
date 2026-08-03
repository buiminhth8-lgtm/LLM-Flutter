from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.repetition import RepetitionEvaluator


def test_repetition_evaluator_detects_duplicate_sentence():
    result = RepetitionEvaluator().evaluate(
        EvaluationInput("chapter", "c1", "p1", "c1", "夜色沉入旧城。夜色沉入旧城。林烬停下。")
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["duplicate_sentence_count"] == 1
    assert any(item.category == "repetition" for item in result.findings)

