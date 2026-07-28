from __future__ import annotations

import os
import sys
from types import SimpleNamespace


def test_server_import_does_not_require_click() -> None:
    sys.modules.pop("llm_studio.server", None)
    sys.modules.pop("click", None)

    import llm_studio.server  # noqa: F401

    assert "click" not in sys.modules


def test_server_parser_defaults() -> None:
    from llm_studio.server import build_parser

    args = build_parser().parse_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000


def test_server_main_sets_config_and_calls_uvicorn(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_run(app: str, **kwargs: object) -> None:
        calls["app"] = app
        calls["kwargs"] = kwargs

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))
    monkeypatch.delenv("LLM_STUDIO_CONFIG", raising=False)

    from llm_studio.server import main

    main(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
            "--config",
            "custom.yaml",
            "--log-level",
            "warning",
        ]
    )

    assert os.environ["LLM_STUDIO_CONFIG"] == "custom.yaml"
    assert calls["app"] == "llm_studio.api_server:app"
    assert calls["kwargs"] == {
        "host": "127.0.0.1",
        "port": 9000,
        "reload": False,
        "log_level": "warning",
    }
