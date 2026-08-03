# Windows 发布指南

## 打包

```powershell
.\scripts\package_windows.ps1
```

## 发布前检查

- 后端测试通过。
- Flutter analyze/test/build 通过。
- 诊断导出已脱敏。
- 发布说明已更新。
- 不包含本机绝对路径、API Key、Cookie、模型权重。

## 标签

Release Candidate 标签应在验证通过后创建。
