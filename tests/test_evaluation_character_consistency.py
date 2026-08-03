from llm_studio.evaluation.evaluators.base import EvaluationInput
from llm_studio.evaluation.evaluators.character_consistency import CharacterConsistencyEvaluator


def test_character_consistency_detects_unknown_speaker():
    result = CharacterConsistencyEvaluator().evaluate(
        EvaluationInput(
            "chapter",
            "c1",
            "p1",
            "c1",
            "林烬说我要查清真相。陌生人说道你来晚了。",
            references={"characters": [{"name": "林烬", "speech_style": "克制"}]},
        )
    )
    metrics = {item.metric_name: item.metric_value for item in result.metrics}
    assert metrics["unknown_character_mentions"] >= 1
    assert any(item.category == "character" for item in result.findings)

