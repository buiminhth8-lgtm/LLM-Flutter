from tests.test_stage12_version_api import _stage12_client


def test_health_api_has_quick_and_full_checks(monkeypatch, tmp_path):
    client = _stage12_client(tmp_path, monkeypatch)

    quick = client.get("/v1/health")
    full = client.get("/v1/health/full")

    assert quick.status_code == 200
    assert full.status_code == 200
    assert quick.json()["mode"] == "quick"
    assert full.json()["mode"] == "full"
    assert quick.json()["checks"]["server"]["status"] == "ok"
    assert full.json()["checks"]["job_queue"]["status"] == "ok"
    assert full.json()["checks"]["model_registry"]["status"] == "ok"
    assert full.json()["checks"]["adapter_registry"]["status"] == "ok"
