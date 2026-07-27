import pytest

from llm_studio.runtime.capabilities import RuntimeCapabilities
from llm_studio.runtime.model_load_policy import choose_model_load_policy


class FakeConfig:
    inference = {}

    def __init__(self, runtime=None):
        self._runtime = {
            "device": "auto",
            "dtype": "auto",
            "quantization": "auto",
            "attention_backend": "auto",
            "max_gpu_memory": "7GiB",
            "max_cpu_memory": "24GiB",
            "cpu_offload": True,
            "trust_remote_code": False,
        }
        if runtime:
            self._runtime.update(runtime)

    @property
    def runtime(self):
        return self._runtime

    def get(self, key, default=None):
        return self._runtime if key == "runtime" else default


def caps(cuda=True, bf16=True, bnb=True):
    return RuntimeCapabilities(
        python_version="3.12.0",
        torch_version="2.x",
        cuda_available=cuda,
        cuda_runtime="13.2",
        gpu_name="NVIDIA GeForce RTX 5060 Laptop GPU" if cuda else None,
        compute_capability=(12, 0) if cuda else None,
        total_vram_bytes=8 * 1024**3 if cuda else None,
        bf16_supported=bf16,
        bitsandbytes_installed=bnb,
        bitsandbytes_4bit_usable=bnb,
        llama_cpp_installed=False,
        llama_cpp_cuda_enabled=False,
        gptqmodel_installed=False,
    )


def test_3b_model_prefers_bf16_on_8gb_cuda():
    policy = choose_model_load_policy("Qwen2.5-3B-Instruct", FakeConfig(), caps())
    assert policy.dtype == "bfloat16"
    assert policy.quantization == "none"
    assert policy.max_memory[0] == "7GiB"


def test_7b_model_auto_selects_bnb4_when_probe_usable():
    policy = choose_model_load_policy("Qwen2.5-7B-Instruct", FakeConfig(), caps())
    assert policy.quantization == "bnb4"


def test_bnb_probe_failure_auto_falls_back():
    policy = choose_model_load_policy("Qwen2.5-7B-Instruct", FakeConfig(), caps(bnb=False))
    assert policy.quantization == "none"


def test_explicit_bnb4_failure_raises():
    with pytest.raises(RuntimeError):
        choose_model_load_policy(
            "Qwen2.5-7B-Instruct",
            FakeConfig({"quantization": "bnb4"}),
            caps(bnb=False),
        )


def test_trust_remote_code_default_false():
    policy = choose_model_load_policy("Qwen2.5-3B-Instruct", FakeConfig(), caps())
    assert policy.trust_remote_code is False
