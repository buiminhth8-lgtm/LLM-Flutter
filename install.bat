@echo off
echo ================================================
echo   LLM Studio - 快速安装脚本 (Windows)
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create venv
echo [1/3] 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

:: Install dependencies
echo [2/3] 安装依赖（可能需要几分钟）...
pip install --upgrade pip
pip install -r requirements.txt

:: Install as package
echo [3/3] 安装 LLM Studio...
pip install -e .

echo.
echo ================================================
echo   安装完成！
echo.
echo   启动 Web 界面:  llm-studio ui
echo   查看帮助:       llm-studio --help
echo   查看系统信息:   llm-studio info
echo ================================================
pause
