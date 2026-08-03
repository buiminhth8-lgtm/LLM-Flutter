# Novel Studio 阶段 7：数据集版本冻结与配方推荐

本文档为阶段归档版，已删除重复验收长列表，保留范围、边界、数据资产和前后置关系。

## 范围

冻结 DatasetVersion，生成 manifest、训练/验证拆分和训练配方建议。

## 主要资产

- 后端领域模块按阶段分层复用。
- Flutter 页面只调用后端 API，不在前端实现核心业务事实。
- 数据库表与记录均保持阶段边界。

## 边界

确认配方不等于启动 Fine-tune。

## 验收

- 后端测试通过。
- Flutter analyze/test 按环境执行。
- 能力清单状态与阶段目标一致。
- 不保存 API Key、Cookie、Authorization 或本机敏感绝对路径。

## 相关

返回 [Novel Studio 路线图](NOVEL_STUDIO_ROADMAP.md)。
