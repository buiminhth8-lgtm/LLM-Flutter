# 开发指南

## 后端

```powershell
python -m pip install -r requirements/base.txt
python -m pip install -r requirements/web.txt
python -m pip install -r requirements/dev.txt
python -m pip install -e .
python -m llm_studio.server --help
```

## Flutter

```powershell
cd apps\flutter_studio
flutter pub get
flutter analyze
flutter test
```

## 验证

```powershell
python -m compileall llm_studio
python -m pytest
```

## 约定

- 后端业务逻辑放在对应领域模块。
- Flutter 不拼接最终 Prompt，不直接调用模型。
- 敏感信息必须脱敏。
