from tests.evaluation_stage11_utils import make_evaluation_service, make_project, run


def test_evaluation_report_generation_separates_auto_and_manual(tmp_path):
    service = make_evaluation_service(tmp_path)
    project, chapter = make_project(service.novel_service)
    detail = run(
        service.run_sync(
            {
                "name": "report eval",
                "target_type": "chapter",
                "target_id": chapter["id"],
                "project_id": project["id"],
                "evaluator_config": {"enabled_evaluators": ["repetition"]},
            }
        )
    )
    service.add_manual_score(detail["run_id"], {"overall_score": 5, "notes": "人工评分"})
    report = service.generate_report(detail["run_id"])
    assert report["report"]["automatic_evaluation"]["case_count"] == 1
    assert report["report"]["manual_evaluation"]["score_count"] == 1
    assert "自动评估" in report["summary_text"]

