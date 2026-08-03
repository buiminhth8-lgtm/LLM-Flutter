def test_evaluation_api_run_sync_manual_report_and_archive(monkeypatch, tmp_path):
    from tests.test_novel_projects_api import _client

    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Stage 11"}).json()
    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={
            "title": "黑市",
            "draft_content": "林烬进入黑市。林烬进入黑市。陌生人说道你来晚了。",
            "summary": "进入黑市",
        },
    ).json()
    client.post(
        f"/v1/novels/projects/{project['id']}/characters",
        json={"name": "林烬", "speech_style": "克制"},
    )
    response = client.post(
        "/v1/evaluation/run-sync",
        json={
            "name": "API eval",
            "target_type": "chapter",
            "target_id": chapter["id"],
            "project_id": project["id"],
            "evaluator_config": {"enabled_evaluators": ["repetition", "character_consistency"]},
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    assert response.json()["status"] == "completed"
    assert client.get(f"/v1/evaluation/runs/{run_id}/metrics").json()["data"]
    findings = client.get(f"/v1/evaluation/runs/{run_id}/findings").json()["data"]
    assert findings
    patched = client.patch(
        f"/v1/evaluation/findings/{findings[0]['finding_id']}",
        json={"status": "dismissed"},
    )
    assert patched.json()["status"] == "dismissed"
    manual = client.post(
        f"/v1/evaluation/runs/{run_id}/manual-score",
        json={"overall_score": 4, "dimensions": {"style": 4}, "notes": "人工确认"},
    )
    assert manual.status_code == 200
    report = client.post(f"/v1/evaluation/runs/{run_id}/report")
    assert report.status_code == 200
    assert client.get(f"/v1/evaluation/reports/{report.json()['report_id']}").status_code == 200
    assert client.get("/v1/evaluation/runs").json()["data"]
    assert client.delete(f"/v1/evaluation/runs/{run_id}").json()["status"] == "archived"


def test_evaluation_api_missing_target_returns_stable_error(monkeypatch, tmp_path):
    from tests.test_novel_projects_api import _client

    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/v1/evaluation/run-sync",
        json={"name": "bad", "target_type": "chapter", "target_id": "missing"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "EVALUATION_TARGET_NOT_FOUND"

