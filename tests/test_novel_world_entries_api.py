from tests.test_novel_projects_api import _client


def test_world_plot_and_timeline_crud(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Novel"}).json()

    world = client.post(
        f"/v1/novels/projects/{project['id']}/world",
        json={"category": "location", "title": "北境", "content": "寒冷边地"},
    )
    assert world.status_code == 200
    assert world.json()["category"] == "location"

    worlds = client.get(f"/v1/novels/projects/{project['id']}/world")
    assert len(worlds.json()["data"]) == 1

    thread = client.post(
        f"/v1/novels/projects/{project['id']}/plot-threads",
        json={"title": "王位谜案", "description": "主线"},
    )
    assert thread.status_code == 200
    assert thread.json()["status"] == "open"

    event = client.post(
        f"/v1/novels/projects/{project['id']}/timeline",
        json={"title": "序章事件"},
    )
    assert event.status_code == 200
    assert event.json()["event_order"] == 1

    assert len(client.get(f"/v1/novels/projects/{project['id']}/plot-threads").json()["data"]) == 1
    assert len(client.get(f"/v1/novels/projects/{project['id']}/timeline").json()["data"]) == 1
