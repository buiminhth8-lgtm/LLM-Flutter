# LLM-Studio

LLM-Studio 是面向 Windows 本地大模型工作的桌面应用。当前形态由 Flutter Windows 客户端和 Python FastAPI 后端组成，重点支持本地模型管理、聊天、下载、诊断，以及 Novel Studio 小说生产闭环。

## 当前状态

- 桌面客户端：`apps/flutter_studio/`
- 后端服务：`llm_studio/`
- 默认配置：`config.yaml`
- 运行数据：`data/`（已通过 `.gitignore` 排除）
- Novel Studio：阶段 0～12 已整理为产品化闭环；入口由 `/v1/capabilities` 和 `features.novel_studio.enabled` 控制。
- Prompt Studio：内置 24 个中文小说创作默认模板，幂等安装、按 `builtin_key` 匹配且不覆盖用户修改。
- Model Gateway：已实现 provider-neutral 调用层核心（FakeProvider / LocalRuntimeProvider / ModelGatewayService），WritingService 的本地生成已路由到 ModelGateway；默认仍使用本地模型，未接入在线 Provider。

## 快速启动

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```

```powershell
cd apps\flutter_studio
flutter run -d windows
```

如果桌面端未显示 Novel 模块，请确认：

1. `config.yaml` 中 `features.novel_studio.enabled: true`。
2. 后端已重启，`GET /v1/capabilities` 返回 Novel 相关能力。
3. Flutter 连接的是同一个后端地址。
4. 左侧导航需要刷新能力后才会显示 Novel Studio 入口。

## 常用验证

```powershell
python -m compileall llm_studio
python -m pytest
python -m llm_studio.server --help
```

```powershell
cd apps\flutter_studio
flutter analyze
flutter test
```

## 文档入口

所有文档已整理为中文归档版，统一入口见 [docs/README.md](docs/README.md)。

重要文档：

- [Novel Studio 路线图](docs/NOVEL_STUDIO_ROADMAP.md)
- [能力清单](docs/CAPABILITIES.md)
- [Flutter 客户端](docs/FLUTTER_CLIENT.md)
- [Windows 发布指南](docs/WINDOWS_RELEASE_GUIDE.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)
- [认证恢复](docs/AUTH_RECOVERY.md)
- [下载生命周期](docs/DOWNLOADS.md)

## 边界

- 不保存 API Key、Cookie、Authorization、绝对敏感路径到生成记录或诊断包。
- `Save to Draft` 只写章节草稿，不等同于 Revision。
- Dataset、Fine-tune、Adapter Evaluation、Memory、Evaluation 均为显式用户动作。
- 已冻结的 DatasetVersion 不应被原地修改。
