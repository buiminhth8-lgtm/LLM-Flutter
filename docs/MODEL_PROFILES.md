# Model Profiles

## 1. 目标

将模型调用配置抽象为可持久化的 model profile：provider、模型标识、默认生成
参数、能力摘要、隐私策略与连接摘要。本阶段只支持本地 Provider，为未来的
OpenAI-compatible / DeepSeek Provider 预留字段，但不实现任何在线调用。

## 2. 当前支持范围

Supported:

- `local_runtime`
- `fake`

Not implemented:

- `openai_compatible`
- `deepseek`
- online API key storage
- Writing provider switch

Flutter provider switch will be implemented in a later phase.

## 3. model_profiles 表

`llm_studio/model_gateway/migrations.py` 创建 `model_profiles` 表：

- `id`：UUID。
- `name`：用户可见名称。
- `provider`：`local_runtime` / `fake`；`openai_compatible` / `deepseek`
  仅文档预留，API 创建时直接拒绝。
- `model`：本地模型 id 或 provider model name（`local_runtime` 对应现有
  model_id）。
- `status`：`enabled` / `disabled` / `archived`。
- `default_params_json`：temperature、top_p、max_tokens 等默认生成参数。
- `capabilities_json`：stream、json_output、tool_calls、vision、
  max_context_tokens、max_output_tokens。
- `privacy_policy_json`：offline_only、confirm_required、allow_cloud 等预留策略。
- `connection_json`：仅保存非敏感连接摘要；禁止 API Key / token /
  Authorization / secret。
- `metadata_json`：builtin、builtin_key、source、created_by、notes 等。
- `is_default`：是否为默认 profile（同一时刻最多一个 enabled default）。

索引：`provider`、`status`、`is_default`。

## 4. API

`/v1/model-profiles`：

- `GET /v1/model-profiles`：列表（可按 provider / status 过滤）。
- `POST /v1/model-profiles`：创建（`local_runtime` / `fake`）。
- `GET /v1/model-profiles/{profile_id}`：详情。
- `PATCH /v1/model-profiles/{profile_id}`：更新。
- `DELETE /v1/model-profiles/{profile_id}`：软删除（归档）。
- `POST /v1/model-profiles/{profile_id}/set-default`：设为默认。
- `GET /v1/model-profiles/default`：当前默认 profile。
- `POST /v1/model-profiles/defaults/ensure`：安装内置 profiles（幂等）。

错误码：`MODEL_PROFILE_NOT_FOUND`（404）、`MODEL_PROFILE_DISABLED`（409）、
`MODEL_PROFILE_INVALID_PROVIDER`、`MODEL_PROFILE_VALIDATION_FAILED`、
`MODEL_PROFILE_SECRET_NOT_ALLOWED`（400）。

## 5. Builtin Profiles

`POST /v1/model-profiles/defaults/ensure` 安装两个内置 profile（按
`metadata.builtin_key` 幂等判断，不覆盖用户修改）：

1. **Fake Test Model**：provider=`fake`，model=`fake`，enabled，非默认，
   `builtin_key=builtin.fake.test.v1`。
2. **Local Runtime Default**：provider=`local_runtime`，model=null，enabled，
   `builtin_key=builtin.local_runtime.default.v1`。

## 6. Default Profile 规则

- 同一时刻最多一个 enabled default profile。
- `set-default` 会先清除其他 profile 的 default 标记。
- 只有 `enabled` profile 可以设为 default。
- 若不存在任何 default profile，`ensure` 会把 Local Runtime Default 设为默认；
  已有用户 default 时不覆盖。

## 7. 安全策略

- `connection` 中出现 `api_key` / `token` / `authorization` / `password` /
  `secret` / `cookie` / `bearer`（大小写不敏感）时直接拒绝
  （`MODEL_PROFILE_SECRET_NOT_ALLOWED`）。
- API 响应只返回脱敏后的 connection 摘要，不返回任何密钥。
- 本阶段不读取任何在线 Provider 的 API Key。

## 8. 后续阶段

- `feat/openai-compatible-provider`：OpenAI-compatible Provider 与在线调用。
- DeepSeek preset。
- Writing Provider 切换 UI 与 Settings 只读 profile 列表页。
- 在线隐私确认（online_privacy_confirmation）与 usage 计量。
