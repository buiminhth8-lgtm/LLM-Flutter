$ErrorActionPreference = "Stop"

Write-Host "Python:"
python -c "import sys; print(sys.executable); print(sys.version); raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 'Python 3.12 x64 is recommended for this project')"

python -c "import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 'No virtual environment detected. Activate .venv first.')"

Write-Host "pip:"
python -m pip --version

Write-Host "Removing existing torch packages..."
python -m pip uninstall -y torch torchvision torchaudio

Write-Host "Installing CUDA PyTorch from PyTorch CUDA 13.2 index..."
python -m pip install --no-cache-dir torch torchvision torchaudio -f https://mirrors.aliyun.com/pytorch-wheels/cu132

python -c @'
import sys
import torch

print("python=", sys.executable)
print("torch=", torch.__version__)
print("torch_path=", torch.__file__)
print("cuda_build=", torch.version.cuda)
print("cuda_available=", torch.cuda.is_available())

if not torch.cuda.is_available():
    raise SystemExit("CUDA is unavailable")
if "+cpu" in torch.__version__:
    raise SystemExit("CPU torch wheel was installed")

print("device=", torch.cuda.get_device_name(0))
print("capability=", torch.cuda.get_device_capability(0))
'@
