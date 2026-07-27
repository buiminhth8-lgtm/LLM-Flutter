$ErrorActionPreference = "Stop"

$env:CMAKE_ARGS = "-DGGML_CUDA=on"
$env:FORCE_CMAKE = "0"
python -m pip install --upgrade --no-cache-dir llama-cpp-python -r requirements\gguf.txt -c requirements\constraints.txt
python -m llm_studio.runtime.diagnostics
