$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt -c requirements\constraints.txt
python -m pip install -e .
