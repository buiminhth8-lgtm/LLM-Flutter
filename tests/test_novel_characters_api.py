from tests.test_novel_projects_api import _client


def test_character_crud(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "Novel"}).json()

    created = client.post(
        f"/v1/novels/projects/{project['id']}/characters",
        json={"name": "阿宁", "role": "protagonist", "aliases": "[\"宁\"]"},
    )
    assert created.status_code == 200
    assert created.json()["name"] == "阿宁"

    listed = client.get(f"/v1/novels/projects/{project['id']}/characters")
    assert len(listed.json()["data"]) == 1

    patched = client.patch(
        f"/v1/novels/characters/{created.json()['id']}",
        json={"speech_style": "短句"},
    )
    assert patched.status_code == 200
    assert patched.json()["speech_style"] == "短句"

    deleted = client.delete(f"/v1/novels/characters/{created.json()['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
