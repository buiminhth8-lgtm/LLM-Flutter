# Novel Studio Stage 12: UI 产品化与 Windows 发布验收

Stage 12 是产品化与发布验收层，不新增小说业务核心能力。它把 Stage 1–11 已有能力整理为一个可用的 Flutter Windows 桌面工作流，并补齐本地后端健康检查、版本信息、诊断导出、备份恢复和发布清单。

## 范围

- Novel Studio Dashboard：统一入口、快捷操作、流程图、健康摘要和近期活动。
- 统一导航：Projects、Prompt Studio、Context、Writing、Revision、Dataset、Fine-tune、Adapter Eval、Memory、Evaluation。
- 统一 UI 状态：empty、error、loading、capability gate、diagnostics hint、copyable error、retry panel。
- Settings：后端连接测试、Diagnostics 入口、Release Notes 入口。
- Diagnostics：`/v1/diagnostics/*` 与脱敏 zip 导出。
- Health：`/v1/health`、`/v1/health/full`。
- Version：`/v1/version`。
- Windows scripts：启动、环境检查、诊断、备份、恢复、发布打包。

## 不包含内容

- 不新增 Novel、Prompt、Context、Writing、Revision、Dataset、Fine-tune、Memory、Evaluation 的核心业务能力。
- 不启动训练。
- 不自动创建训练样本。
- 不自动修改正文或覆盖 `final_content`。
- 不自动激活 Adapter。
- 不恢复 Hugging Face Provider。
- 不引入云端依赖。

## Dashboard 旅程

1. Project → Chapter → Character / World Bible。
2. Prompt Studio → Context Preview。
3. Writing 生成草稿，Save to Draft 仍由用户显式执行。
4. Revision 人工修订，Diff 与评分持久化。
5. Dataset Builder 只消费审核通过且用户选择的候选。
6. DatasetVersion 冻结后才能进入 Fine-tune。
7. Fine-tune 完成后注册 Adapter，但不自动激活。
8. Adapter Evaluation / Full Evaluation 显式评估。
9. Memory/RAG 由用户显式检索或注入。

## Diagnostics 脱敏边界

诊断包包含运行时摘要、版本、系统摘要、pip freeze、脱敏配置、模型摘要、磁盘摘要和 capabilities。它不包含：

- API Key、Cookie、Authorization header；
- 模型权重、adapter 权重、训练 checkpoint；
- RAG 文档正文、小说正文、训练样本全文；
- 本地绝对模型路径。

## Stage 13 维护建议

- 增加真实安装器签名流程。
- 增加自动 UI 截图验收。
- 为长任务统一 toast/notification center。
- 将 release checklist 接入 CI。
