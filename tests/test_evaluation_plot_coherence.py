from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.plot_coherence import PlotCoherenceEvaluator


def test_plot_coherence_detects_low_goal_coverage():
    result = PlotCoherenceEvaluator().evaluate(
        EvaluationInput(
            "chapter",
            "c1",
            "p1",
            "c1",
            "这一章一直描写雨声和墙壁。",
            context={"current_chapter_goal": "主角进入黑市发现灵骨交易"},
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["chapter_goal_coverage"] < 0.35
    assert any(item.category == "plot" for item in result.findings)

