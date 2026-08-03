# Novel Studio 阶段 12：UI 产品化与 Windows 发布验收

本文档为阶段归档版，已删除重复验收长列表，保留范围、边界、数据资产和前后置关系。

## 范围

完善 Flutter Windows 产品界面、统一导航、诊断、发布脚本、Windows 验收和 Release Candidate 资料。

## 主要资产

- 后端领域模块按阶段分层复用。
- Flutter 页面只调用后端 API，不在前端实现核心业务事实。
- 数据库表与记录均保持阶段边界。

## 边界

不新增核心生成、训练、RAG、评估业务能力。

## 验收

- 后端测试通过。
- Flutter analyze/test 按环境执行。
- 能力清单状态与阶段目标一致。
- 不保存 API Key、Cookie、Authorization 或本机敏感绝对路径。

## 相关

返回 [Novel Studio 路线图](NOVEL_STUDIO_ROADMAP.md)。
