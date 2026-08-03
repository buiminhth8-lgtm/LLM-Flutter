# 发布检查清单

## 后端

```powershell
python -m compileall llm_studio
python -m pytest
python -m llm_studio.server --help
```

## Flutter

```powershell
cd apps\flutter_studio
flutter analyze
flutter test
flutter build windows
```

## Windows

- 检查启动脚本。
- 检查诊断导出脱敏。
- 检查备份与恢复脚本。
- 检查发布说明。
- 创建 Release Candidate 标签前确认工作区干净。
