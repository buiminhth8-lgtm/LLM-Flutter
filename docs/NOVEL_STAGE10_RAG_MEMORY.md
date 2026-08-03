# Novel Studio 阶段 10：长篇记忆 / RAG 增强

本文档为阶段归档版，已删除重复验收长列表，保留范围、边界、数据资产和前后置关系。

## 范围

维护章节摘要、记忆文档、索引状态、检索预览，并向 ContextAssembler 注入 retrieved_memory。

## 主要资产

- 后端领域模块按阶段分层复用。
- Flutter 页面只调用后端 API，不在前端实现核心业务事实。
- 数据库表与记录均保持阶段边界。

## 边界

不替代人工修订，不自动写正文。

## 验收

- 后端测试通过。
- Flutter analyze/test 按环境执行。
- 能力清单状态与阶段目标一致。
- 不保存 API Key、Cookie、Authorization 或本机敏感绝对路径。

## 相关

返回 [Novel Studio 路线图](NOVEL_STUDIO_ROADMAP.md)。
