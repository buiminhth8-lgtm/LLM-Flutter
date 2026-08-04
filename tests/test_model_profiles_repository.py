import pytest

from llm_studio.model_gateway import (
    MODEL_PROFILE_NOT_FOUND,
    MODEL_PROFILE_VALIDATION_FAILED,
    ModelGatewayError,
)
from llm_studio.model_gateway.profiles import ModelProfileCreate
from llm_studio.model_gateway.repository import ModelProfileRepository


def _repo(tmp_path) -> ModelProfileRepository:
    return ModelProfileRepository(tmp_path / "gateway.sqlite")


def _create(repo: ModelProfileRepository, **extra) -> dict:
    return ModelProfileCreate(
        name=extra.pop("name", "Local Qwen"),
        provider=extra.pop("provider", "local_runtime"),
        model=extra.pop("model", "qwen3-8b"),
        default_params=extra.pop(
            "default_params", {"temperature": 0.8, "max_tokens": 1400}
        ),
        capabilities=extra.pop(
            "capabilities", {"stream": True, "max_context_tokens": 8192}
        ),
        metadata=extra.pop("metadata", {"source": "user"}),
        **extra,
    )


def test_create_local_runtime_profile(tmp_path):
    repo = _repo(tmp_path)

    profile = repo.create(_create(repo))

    assert profile.provider == "local_runtime"
    assert profile.model == "qwen3-8b"
    assert profile.status == "enabled"
    assert profile.default_params["max_tokens"] == 1400


def test_create_fake_profile(tmp_path):
    repo = _repo(tmp_path)

    profile = repo.create(_create(repo, provider="fake", model="fake"))

    assert profile.provider == "fake"
    assert profile.model == "fake"


def test_list_by_provider_and_status(tmp_path):
    repo = _repo(tmp_path)
    repo.create(_create(repo, name="A", provider="local_runtime"))
    repo.create(_create(repo, name="B", provider="fake", model="fake"))

    local = repo.list(provider="local_runtime")
    fake = repo.list(provider="fake")

    assert [p.name for p in local] == ["A"]
    assert [p.name for p in fake] == ["B"]
    assert repo.list(status="disabled") == []


def test_get_by_id(tmp_path):
    repo = _repo(tmp_path)
    created = repo.create(_create(repo))

    fetched = repo.get(created.id)

    assert fetched == created
    assert repo.get("missing") is None


def test_update_default_params(tmp_path):
    repo = _repo(tmp_path)
    created = repo.create(_create(repo))

    updated = repo.update(
        created.id,
        {"default_params": {"temperature": 0.6, "max_tokens": 512}},
    )

    assert updated.default_params == {"temperature": 0.6, "max_tokens": 512}
    assert updated.name == created.name


def test_archive_profile_and_list_excludes_archived(tmp_path):
    repo = _repo(tmp_path)
    created = repo.create(_create(repo))

    archived = repo.archive(created.id)

    assert archived.status == "archived"
    assert created.id not in {p.id for p in repo.list()}
    assert repo.get(created.id).status == "archived"


def test_set_default_clears_other_defaults(tmp_path):
    repo = _repo(tmp_path)
    first = repo.create(_create(repo, name="First", is_default=True))
    second = repo.create(_create(repo, name="Second"))

    repo.set_default(second.id)

    assert repo.get(first.id).is_default is False
    assert repo.get(second.id).is_default is True
    assert repo.get_default().id == second.id


def test_json_fields_roundtrip(tmp_path):
    repo = _repo(tmp_path)
    profile = repo.create(
        _create(
            repo,
            capabilities={"stream": True, "vision": False},
            privacy_policy={"mode": "offline_only"},
            connection={"label": "local"},
            metadata={"builtin": True, "notes": "x"},
        )
    )

    fetched = repo.get(profile.id)

    assert fetched.capabilities == {"stream": True, "vision": False}
    assert fetched.privacy_policy == {"mode": "offline_only"}
    assert fetched.connection == {"label": "local"}
    assert fetched.metadata == {"builtin": True, "notes": "x"}


def test_get_missing_raises_not_found_for_update(tmp_path):
    repo = _repo(tmp_path)

    with pytest.raises(ModelGatewayError) as exc_info:
        repo.update("missing", {"name": "x"})

    assert exc_info.value.code == MODEL_PROFILE_NOT_FOUND


def test_update_cannot_change_provider(tmp_path):
    repo = _repo(tmp_path)
    created = repo.create(_create(repo))

    with pytest.raises(ModelGatewayError) as exc_info:
        repo.update(created.id, {"provider": "fake"})

    assert exc_info.value.code == MODEL_PROFILE_VALIDATION_FAILED
