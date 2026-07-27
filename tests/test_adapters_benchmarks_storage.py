import json
from pathlib import Path

from llm_studio.adapters.scanner import AdapterScanner
from llm_studio.benchmarks import BenchmarkConfig, BenchmarkRunner
from llm_studio.benchmarks.metrics import tokens_per_second
from llm_studio.config_io import redact_config
from llm_studio.diagnostics.export import redact_path
from llm_studio.storage.disk_usage import path_size


class FakeRunner:
    def __init__(self):
        self.loaded = False
        self.tokenizer = self._tokenize

    def load(self):
        self.loaded = True

    def unload(self):
        self.loaded = False

    def generate_stream(self, messages, generation_config=None):
        yield "hello"
        yield " world"

    def _tokenize(self, text, add_special_tokens=False):
        return {"input_ids": list(text)}


def test_adapter_scanner_reads_config(tmp_path):
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_config.json").write_text(
        json.dumps(
            {
                "base_model_name_or_path": "base",
                "peft_type": "LORA",
                "task_type": "CAUSAL_LM",
                "r": 8,
                "lora_alpha": 16,
                "target_modules": ["q_proj", "v_proj"],
            }
        ),
        encoding="utf-8",
    )
    (adapter / "adapter_model.safetensors").write_bytes(b"x")

    info = AdapterScanner(tmp_path).scan()[0]

    assert info.rank == 8
    assert info.compatible
    assert "q_proj" in info.target_modules


def test_benchmark_metrics_and_repository(tmp_path):
    class Config:
        config_path = tmp_path / "config.yaml"

        def get(self, key, default=None):
            data = {
                "models": {
                    "root_dir": str(tmp_path / "models"),
                    "temp_dir": str(tmp_path / "downloads"),
                    "metadata_cache": str(tmp_path / "model_index.json"),
                    "adapters_dir": str(tmp_path / "adapters"),
                },
                "storage": {
                    "trash_dir": str(tmp_path / "trash"),
                    "benchmarks_dir": str(tmp_path / "benchmarks"),
                    "jobs_dir": str(tmp_path / "jobs"),
                    "diagnostics_dir": str(tmp_path / "diagnostics"),
                },
            }
            return data.get(key, default)

    assert tokens_per_second(10, 0.1, 1.1) == 10
    result = BenchmarkRunner(Config(), lambda _: FakeRunner()).run(
        BenchmarkConfig(model_id="fake", warmup_runs=0, measured_runs=1, context_lengths=(128,))
    )
    assert result.runs
    assert result.runs[0].input_tokens >= 128
    assert list((tmp_path / "benchmarks").glob("*.json"))
    assert list((tmp_path / "benchmarks").glob("*.md"))


def test_redaction_and_path_size(tmp_path):
    data = redact_config({"runtime": {}, "huggingface": {"token": "secret"}, "api": {"api_key": "x"}})
    assert data["huggingface"]["token"] == "<redacted>"
    assert data["api"]["api_key"] == "<redacted>"
    file = tmp_path / "x.txt"
    file.write_text("abc", encoding="utf-8")
    assert path_size(file) == 3
    assert "%USERPROFILE%" in redact_path(str(Path.home() / "secret"))
