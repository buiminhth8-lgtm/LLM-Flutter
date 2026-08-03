from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.local_model_judge import LocalModelJudgeEvaluator
from tests.evaluation_stage11_utils import FakeRuntimeBridge, run


def test_local_model_judge_uses_fake_runtime():
    result = run(
        LocalModelJudgeEvaluator(FakeRuntimeBridge(), "fake-model").evaluate(
            EvaluationInput("chapter", "c1", "p1", "c1", "林烬进入黑市。")
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["local_model_judge_score"] == 4
    assert result.findings

