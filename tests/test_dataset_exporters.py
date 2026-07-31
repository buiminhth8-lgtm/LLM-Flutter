from __future__ import annotations

import json

from llm_studio.datasets.exporters import DatasetJsonlExporter


def test_sft_jsonl_export_is_utf8_one_json_per_line_and_safe_path(tmp_path):
    exporter = DatasetJsonlExporter(tmp_path / "data" / "datasets")
    result = exporter.export(
        {"dataset_id": "dataset-1", "name": "Novel", "type": "sft", "status": "ready"},
        [
            {
                "sample_id": "sample-1",
                "revision_id": "rev-1",
                "project_id": "project-1",
                "instruction": "写小说",
                "input": "设定",
                "output": "正文",
                "status": "approved",
            }
        ],
        export_format="sft_jsonl",
        file_name="../unsafe.jsonl",
    )

    assert result["export_path"].startswith("datasets/dataset-1/exports/")
    export_path = tmp_path / "data" / result["export_path"]
    lines = export_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["output"] == "正文"
    assert payload["metadata"]["revision_id"] == "rev-1"
