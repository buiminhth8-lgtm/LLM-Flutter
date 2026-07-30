from tests.test_novel_projects_api import _client


def test_volume_chapter_scene_crud(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Novel"}).json()

    volume = client.post(
        f"/v1/novels/projects/{project['id']}/volumes",
        json={"title": "第一卷"},
    )
    assert volume.status_code == 200
    assert volume.json()["volume_index"] == 1

    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "第一章", "volume_id": volume.json()["id"], "draft_content": "你好 world"},
    )
    assert chapter.status_code == 200
    assert chapter.json()["chapter_index"] == 1
    assert chapter.json()["word_count"] == 3

    patched = client.patch(
        f"/v1/novels/chapters/{chapter.json()['id']}",
        json={"draft_content": "新的草稿 content"},
    )
    assert patched.status_code == 200
    assert patched.json()["version"] == 2

    scene = client.post(
        f"/v1/novels/chapters/{chapter.json()['id']}/scenes",
        json={"title": "开场", "content": "第一幕"},
    )
    assert scene.status_code == 200
    assert scene.json()["scene_index"] == 1

    scenes = client.get(f"/v1/novels/chapters/{chapter.json()['id']}/scenes")
    assert len(scenes.json()["data"]) == 1


def test_create_chapter_requires_existing_project(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/v1/novels/projects/missing/chapters",
        json={"title": "No Project"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOVEL_PROJECT_NOT_FOUND"
