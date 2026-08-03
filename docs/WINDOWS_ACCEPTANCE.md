# Windows 验收

## 环境

- Windows 11 x64
- Python 3.12 x64
- Flutter Windows desktop
- 可选 NVIDIA CUDA GPU

## 验收路径

1. 后端可启动。
2. Flutter 可运行。
3. 设置页可保存 API Base 和 API Key。
4. 能力页显示 Novel Studio。
5. 诊断导出不包含敏感信息。
6. Windows build 可完成。

## 命令

```powershell
.\scripts\windows\check_environment.ps1
.\scripts\windows\start_backend.ps1
.\scripts\windows\start_flutter_desktop.ps1
```
