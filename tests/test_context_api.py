from tests.test_novel_projects_api import _client


def create_context_fixture(client):
    project = client.post(
        "/v1/novels/projects",
        json={
            "title": "Stage 3 Novel",
            "genre": "fantasy",
            "target_style": "restrained",
        },
    ).json()
    previous = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "Previous", "chapter_index": 1, "summary": "Reached the city."},
    ).json()
    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "Market", "chapter_index": 2, "outline": "Enter the market."},
    ).json()
    character = client.post(
        f"/v1/novels/projects/{project['id']}/characters",
        json={"name": "Lin", "role": "protagonist", "personality": "calm"},
    ).json()
    world = client.post(
        f"/v1/novels/projects/{project['id']}/world",
        json={
            "category": "location",
            "title": "Black Market",
            "content": "An underground market.",
            "priority": 80,
        },
    ).json()
    return {
        "project": project,
        "previous": previous,
        "chapter": chapter,
        "character": character,
        "world": world,
    }


def test_context_assemble_estimate_and_records(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    fixture = create_context_fixture(client)

    response = client.post(
        "/v1/context/assemble",
        json={
            "project_id": fixture["project"]["id"],
            "chapter_id": fixture["chapter"]["id"],
            "user_variables": {"current_chapter_goal": "Meet the broker."},
            "save_record": True,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["variables"]["previous_chapter_summary"] == "Reached the city."
    assert result["variables"]["current_chapter_goal"] == "Meet the broker."
    assert result["context_id"]
    assert result["estimated_tokens"] > 0

    record = client.get(f"/v1/context/records/{result['context_id']}")
    assert record.status_code == 200
    assert record.json()["context_hash"] == result["context_hash"]

    listed = client.get(
        "/v1/context/records",
        params={"project_id": fixture["project"]["id"]},
    )
    assert listed.status_code == 200
    assert listed.json()["data"][0]["context_id"] == result["context_id"]

    estimate = client.post("/v1/context/estimate", json={"text": "中文 and English"})
    assert estimate.status_code == 200
    assert estimate.json()["estimated_tokens"] > 0


def test_context_rejects_cross_project_chapter(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    first = create_context_fixture(client)
    second = client.post("/v1/novels/projects", json={"title": "Other"}).json()

    response = client.post(
        "/v1/context/assemble",
        json={
            "project_id": second["id"],
            "chapter_id": first["chapter"]["id"],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONTEXT_CHAPTER_NOT_FOUND"
