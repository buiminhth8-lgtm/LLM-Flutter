# Windows 桌面运行说明

当前 Flutter 第一平台是 Windows Desktop。后端不打包 exe，不使用 CLI，不依赖 click，也不依赖旧的 `llm-studio.exe`。推荐启动方式始终是纯 Python 服务：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

旧虚拟环境中如果仍残留 `venv\Scripts\llm-studio.exe`，它只是历史 `console_scripts` 产物，当前 Flutter 不会调用它。

## 后端准备

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements\base.txt
python -m pip install -r requirements\web.txt
python -m pip install -e .
```

启动后端：

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
```

## Flutter Windows

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
flutter build windows
flutter run -d windows
```

也可以从仓库根目录运行脚本：

```powershell
.\scripts\test_flutter.ps1
.\scripts\flutter_build_windows.ps1
.\scripts\flutter_run_windows.ps1
```

## 后端模式

Settings 页面支持两种模式：

- Local backend：Flutter 先检查 `/health`，如果后端未运行，则通过 `python -m llm_studio.server` 自动启动本地后端。
- Remote backend：Flutter 只连接已配置的 API Base URL，不启动本地进程。

本地后端启动时可以配置：

- Python 可执行文件路径。
- 项目根目录。
- 是否应用启动时自动启动后端。
- 是否应用退出时关闭由 Flutter 启动的后端。

后端 stdout/stderr 会显示在 Settings 页面，并在显示和复制前进行脱敏处理。

## 常见检查

- `/health` 返回 200 说明后端服务已运行。
- `/v1/capabilities` 是前端功能展示依据。
- 首次启动如果返回 `requires_setup=true`，Flutter 应显示初始化页面而不是普通登录页。
- Chat 无模型时应禁用输入，并提示先加载模型。
- Downloads 页面在 `total_bytes=null` 时显示不确定进度，不伪造百分比。
- Diagnostics 导出包不应包含 API Key、Token、Cookie、模型权重或 RAG 文档正文。
