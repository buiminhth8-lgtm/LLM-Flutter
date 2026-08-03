import pytest

from llm_studio.evaluation.errors import EvaluationInvalidScoreError, EvaluationTargetNotFoundError
from tests.evaluation_stage11_utils import make_evaluation_service, make_project, run


def test_evaluation_service_run_sync_persists_metrics_findings_and_manual_score(tmp_path):
    service = make_evaluation_service(tmp_path)
    project, chapter = make_project(service.novel_service)

    detail = run(
        service.run_sync(
            {
                "name": "chapter eval",
                "target_type": "chapter",
                "target_id": chapter["id"],
                "project_id": project["id"],
                "context": {"current_chapter_goal": "进入黑市发现灵骨交易"},
                "evaluator_config": {"enabled_evaluators": ["repetition", "plot_coherence"]},
            }
        )
    )
    assert detail["status"] == "completed"
    run_id = detail["run_id"]
    metrics = service.get_metrics(run_id)
    assert {item["metric_name"] for item in metrics} >= {"repetition_ratio", "plot_coherence_score"}
    manual = service.add_manual_score(
        run_id,
        {"overall_score": 4, "dimensions": {"style": 4}, "notes": "人工确认可用"},
    )
    assert manual["overall_score"] == 4
    findings = service.get_findings(run_id)
    updated = service.update_finding_status(findings[0]["finding_id"], "acknowledged")
    assert updated["status"] == "acknowledged"


def test_evaluation_service_async_creates_job(tmp_path):
    service = make_evaluation_service(tmp_path, job_queue=True)
    project, chapter = make_project(service.novel_service)

    created = run(
        service.create_run(
            {
                "name": "async eval",
                "target_type": "chapter",
                "target_id": chapter["id"],
                "project_id": project["id"],
                "run_async": True,
                "evaluator_config": {"enabled_evaluators": ["repetition"]},
            }
        )
    )
    assert created["job_id"]
    assert created["status"] in {"queued", "running", "completed"}
    service.job_queue.shutdown(wait=False)


def test_evaluation_service_target_and_score_validation(tmp_path):
    service = make_evaluation_service(tmp_path)
    with pytest.raises(EvaluationTargetNotFoundError):
        run(service.run_sync({"name": "bad", "target_type": "chapter", "target_id": "missing"}))
    project, chapter = make_project(service.novel_service)
    detail = run(
        service.run_sync(
            {
                "name": "score eval",
                "target_type": "chapter",
                "target_id": chapter["id"],
                "project_id": project["id"],
                "evaluator_config": {"enabled_evaluators": ["repetition"]},
            }
        )
    )
    with pytest.raises(EvaluationInvalidScoreError):
        service.add_manual_score(detail["run_id"], {"overall_score": 6})

