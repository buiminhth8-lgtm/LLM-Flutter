$ErrorActionPreference = "Stop"

python -m pip install -r requirements\cuda.txt -c requirements\constraints.txt
python -m llm_studio.runtime.diagnostics
