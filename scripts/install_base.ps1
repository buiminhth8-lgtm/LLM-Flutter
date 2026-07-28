$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip setuptools wheel
python -c @'
import torch

print("torch=", torch.__version__)
print("cuda_available=", torch.cuda.is_available())
if "+cpu" in torch.__version__ or not torch.cuda.is_available():
    raise SystemExit(
        "CUDA PyTorch must be installed before base dependencies. "
        "Run scripts/install_windows_cuda.ps1 first."
    )
'@
python -m pip install -r requirements.txt -c requirements\constraints.txt
python -m pip install -e .
