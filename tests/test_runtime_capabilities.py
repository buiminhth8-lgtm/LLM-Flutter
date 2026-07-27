import builtins
import types

from llm_studio.runtime import capabilities as capmod


def test_detect_runtime_without_torch(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(capmod, "_module_installed", lambda name: False)
    caps = capmod.detect_runtime_capabilities()
    assert caps.torch_version is None
    assert caps.cuda_available is False


def test_detect_llama_cpp_cuda_from_system_info(monkeypatch):
    fake_module = types.SimpleNamespace(llama_print_system_info=lambda: b"CUDA = 1")
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "llama_cpp":
            return fake_module
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(capmod, "_module_installed", lambda name: name == "llama_cpp")
    enabled, detail = capmod.detect_llama_cpp_cuda()
    assert enabled is True
    assert "CUDA" in detail
