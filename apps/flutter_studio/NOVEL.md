# Novel Studio 模块说明

Novel Studio 是 LLM-Studio 的小说生产工作台，入口由后端能力和配置共同控制。

## 显示条件

- `features.novel_studio.enabled: true`
- `/v1/capabilities` 中 Novel 相关能力对前端可见
- Flutter 已刷新能力列表

## 已接入页面

- 小说项目
- 提示词工作室
- 上下文预览
- 写作工作区
- 修订审阅
- 数据集构建
- 数据集版本与训练配方
- 微调中心
- 适配器评估
- 记忆 / RAG
- 评估中心

## 边界

每个阶段保持显式动作：生成不等于修订，修订不等于数据集，确认配方不等于启动训练，评估不改写正文。
