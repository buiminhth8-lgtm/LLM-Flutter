#!/bin/bash
echo "================================================"
echo "  LLM Studio - 快速安装脚本 (macOS / Linux)"
echo "================================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.9+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

# Create venv
echo "[1/3] 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "[2/3] 安装依赖（可能需要几分钟）..."
pip install --upgrade pip
pip install -r requirements.txt

# Install as package
echo "[3/3] 安装 LLM Studio..."
pip install -e .

echo
echo "================================================"
echo "  安装完成！"
echo
echo "  激活环境: source venv/bin/activate"
echo "  启动 Web 界面:  llm-studio ui"
echo "  查看帮助:       llm-studio --help"
echo "  查看系统信息:   llm-studio info"
echo "================================================"
