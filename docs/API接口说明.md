# LLM Studio API 接口说明

LLM Studio 提供基于 **FastAPI** 的 REST API 服务，核心聊天接口兼容 **OpenAI API** 格式，可直接对接 RemoteAssistant、ChatBox、Open WebUI 等第三方客户端。

---

## 1. 启动服务

```bash
# 命令行启动（默认端口 8000）
llm-studio serve

# 指定端口和地址
llm-studio serve --host 0.0.0.0 --port 8080
```

服务启动后，可通过浏览器访问：
- **API 文档（Swagger UI）**：`http://localhost:8000/docs`
- **健康检查**：`http://localhost:8000/health`

---

## 2. 认证机制

LLM Studio 使用 **X-User-ID + X-API-Key** 请求头进行身份认证。

### 2.1 配置

在 `config.yaml` 中启用认证：

```yaml
auth:
  enabled: true
```

> 用户管理已迁移到管理后台（`/admin`），无需手动编辑配置文件。

### 2.1 管理后台

启动 API 服务后，访问管理后台创建和管理 API 用户：

```
http://localhost:8000/admin
```

- 不再提供硬编码默认管理员密码；首次启动读取 `LLM_STUDIO_INITIAL_ADMIN_PASSWORD`，未设置时生成一次性随机初始密码并只在启动日志显示。
- 首次启动自动创建默认 admin 用户和 API Key
- 用户数据持久化在 `data/api_users.json`

管理后台功能：

| 功能       | 说明                                |
|-----------|-------------------------------------|
| 新建用户   | 输入 User ID，自动生成安全 API Key   |
| 查看密钥   | 查看完整 Key 并一键复制              |
| 重置密钥   | 重新生成 API Key（原 Key 立即失效）  |
| 启用/禁用  | 临时禁用用户而不删除                 |
| 删除用户   | 永久删除用户及其 Key                 |
| 修改密码   | 修改管理后台登录密码                 |

### 2.2 请求方式

所有 `/v1/*` 接口需携带认证头：

```
X-User-ID: admin
X-API-Key: sk-llmstudio-admin-key
```

也支持标准 `Authorization: Bearer` 作为 API Key 的备选传递方式（仍需 `X-User-ID`）：

```
X-User-ID: admin
Authorization: Bearer sk-llmstudio-admin-key
```

### 2.3 免认证端点

以下端点无需认证即可访问：

| 端点              | 说明           |
|-------------------|----------------|
| `/health`         | 健康检查        |
| `/docs`           | Swagger UI 文档 |
| `/openapi.json`   | OpenAPI Schema  |
| `/redoc`          | ReDoc 文档      |
| `/admin`          | 管理后台        |
| `/admin/api/*`    | 管理后台 API    |

### 2.4 认证失败响应

```json
{
    "error": {
        "message": "Invalid or missing authentication. Provide X-User-ID and X-API-Key headers.",
        "type": "authentication_error",
        "code": "invalid_api_key"
    }
}
```

HTTP 状态码：**401 Unauthorized**

---

## 3. 接口总览

| 分类     | 方法   | 路径                       | 说明                   |
|----------|--------|----------------------------|------------------------|
| 模型     | GET    | `/v1/models`               | 列出所有可用模型       |
| 模型     | POST   | `/v1/models/load`          | 加载模型到内存         |
| 模型     | POST   | `/v1/models/unload`        | 卸载模型释放内存       |
| 聊天     | POST   | `/v1/chat/completions`     | 聊天补全（OpenAI 兼容）|
| RAG      | POST   | `/v1/rag/ingest`           | 投喂文档到知识库       |
| RAG      | POST   | `/v1/rag/ingest/upload`    | 上传文件到知识库       |
| RAG      | POST   | `/v1/rag/query`            | RAG 检索增强查询       |
| RAG      | GET    | `/v1/rag/status`           | 查看知识库状态         |
| RAG      | POST   | `/v1/rag/clear`            | 清空知识库             |
| 视觉     | POST   | `/v1/vision/analyze`       | 图片识别分析           |
| 视觉     | POST   | `/v1/vision/analyze/upload`| 上传图片进行识别       |
| 视觉     | POST   | `/v1/vision/ocr`           | 图片 OCR 文字识别      |
| 管理     | GET    | `/admin`                   | 管理后台页面           |
| 管理     | POST   | `/admin/api/login`         | 管理后台登录           |
| 管理     | GET    | `/admin/api/users`         | 列出所有 API 用户      |
| 管理     | POST   | `/admin/api/users`         | 创建新用户             |
| 管理     | DELETE | `/admin/api/users/{id}`    | 删除用户               |
| 管理     | POST   | `/admin/api/users/{id}/toggle`    | 启用/禁用用户   |
| 管理     | POST   | `/admin/api/users/{id}/regenerate`| 重置 API Key    |
| 系统     | GET    | `/health`                  | 健康检查               |

---

## 4. 模型管理

### 3.1 列出所有可用模型

```
GET /v1/models
```

返回已加载模型和已下载但未加载的本地模型。`owned_by` 字段标识模型状态：
- `local:loaded` — 已加载到内存，可直接推理
- `local:available` — 已下载，需加载后使用（首次对话时自动加载）
- `local:vision:loaded` — 已加载的视觉模型

**响应示例：**

```json
{
    "object": "list",
    "data": [
        {
            "id": "D:\\models\\Qwen2.5-7B-Instruct",
            "object": "model",
            "owned_by": "local:loaded"
        },
        {
            "id": "D:\\models\\chatglm3-6b",
            "object": "model",
            "owned_by": "local:available"
        }
    ]
}
```

### 3.2 加载模型

```
POST /v1/models/load
```

**请求体：**

```json
{
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "model_type": "text"
}
```

| 参数         | 类型   | 必填 | 说明                                      |
|-------------|--------|------|-------------------------------------------|
| `model`     | string | 是   | 模型路径（本地绝对路径）                    |
| `model_type`| string | 否   | `text`（默认）或 `vision`                  |

**响应：**

```json
{
    "status": "ok",
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "type": "text"
}
```

### 3.3 卸载模型

```
POST /v1/models/unload
```

请求体格式同加载接口。卸载后释放 GPU/内存资源。

---

## 5. 聊天补全（OpenAI 兼容）

```
POST /v1/chat/completions
```

**请求体：**

```json
{
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "messages": [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "你好，请自我介绍一下。"}
    ],
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "stream": false
}
```

| 参数          | 类型    | 必填 | 默认值 | 说明                             |
|--------------|---------|------|--------|----------------------------------|
| `model`      | string  | 是   | —      | 模型路径（未加载会自动加载）       |
| `messages`   | array   | 是   | —      | 消息列表，包含 role 和 content    |
| `temperature`| float   | 否   | 0.7    | 采样温度                          |
| `max_tokens` | int     | 否   | 2048   | 最大生成 token 数                 |
| `top_p`      | float   | 否   | 0.9    | Top-p 采样                        |
| `stream`     | bool    | 否   | false  | 是否启用流式输出（SSE）            |

### 4.1 非流式响应

```json
{
    "id": "chatcmpl-a1b2c3d4",
    "object": "chat.completion",
    "created": 1711459200,
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！我是Qwen，一个由阿里云开发的AI助手..."
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    }
}
```

### 4.2 流式响应（SSE）

设置 `"stream": true` 后，服务端通过 **Server-Sent Events** 逐 token 返回内容。

每个事件的格式为：

```
data: {"id":"chatcmpl-a1b2c3d4","object":"chat.completion.chunk","created":1711459200,"model":"...","choices":[{"index":0,"delta":{"content":"你"},"finish_reason":null}]}

data: {"id":"chatcmpl-a1b2c3d4","object":"chat.completion.chunk","created":1711459200,"model":"...","choices":[{"index":0,"delta":{"content":"好"},"finish_reason":null}]}

...

data: {"id":"chatcmpl-a1b2c3d4","object":"chat.completion.chunk","created":1711459200,"model":"...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**关键字段说明：**
- `object` 为 `chat.completion.chunk`（区别于非流式的 `chat.completion`）
- 内容在 `choices[0].delta.content` 中（区别于非流式的 `choices[0].message.content`）
- 最后一个 chunk 的 `finish_reason` 为 `"stop"`，`delta` 为空对象
- 流结束后发送 `data: [DONE]`

---

## 6. RAG 知识库

### 5.1 投喂文档

```
POST /v1/rag/ingest
```

**请求体：**

```json
{
    "file_path": "D:\\docs\\technical_manual.pdf",
    "directory_path": null,
    "recursive": true
}
```

| 参数             | 类型   | 必填 | 说明                                          |
|-----------------|--------|------|-----------------------------------------------|
| `file_path`     | string | 否   | 单个文件路径                                   |
| `directory_path`| string | 否   | 目录路径（批量投喂，file_path 和 directory_path 至少填一个）|
| `recursive`     | bool   | 否   | 是否递归扫描子目录（默认 true）                 |

支持的文件格式：PDF、DOCX、XLSX、CSV、HTML、PPTX、EPUB、TXT、Markdown、JSON。

**响应：**

```json
{
    "status": "ok",
    "chunks_added": 42,
    "total_chunks": 156
}
```

### 5.2 上传文件到知识库

```
POST /v1/rag/ingest/upload
Content-Type: multipart/form-data
```

通过 `file` 字段上传文件（适用于远程客户端不能直接指定服务端路径的场景）。

### 5.3 RAG 检索查询

```
POST /v1/rag/query
```

**请求体：**

```json
{
    "question": "系统的最大并发用户数是多少？",
    "top_k": 5,
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "temperature": 0.7,
    "max_tokens": 2048
}
```

| 参数          | 类型   | 必填 | 说明                                   |
|--------------|--------|------|----------------------------------------|
| `question`   | string | 是   | 查询问题                                |
| `top_k`      | int    | 否   | 检索最相关的文档片段数量（默认 5）        |
| `model`      | string | 否   | 指定模型路径后，会生成 RAG 增强回答       |
| `temperature`| float  | 否   | 生成回答的采样温度                       |
| `max_tokens` | int    | 否   | 生成回答的最大 token 数                  |

**响应：**

```json
{
    "question": "系统的最大并发用户数是多少？",
    "retrieved_documents": [
        {
            "content": "系统支持最大 10000 并发用户...",
            "source": "technical_manual.pdf",
            "score": 0.8923
        }
    ],
    "answer": "根据技术手册的描述，系统支持最大 10000 并发用户..."
}
```

> 若未指定 `model`，`answer` 为 `null`，仅返回检索到的文档片段。

### 5.4 知识库状态

```
GET /v1/rag/status
```

**响应：**

```json
{
    "status": "ok",
    "document_count": 156,
    "sources": ["technical_manual.pdf", "api_reference.md"]
}
```

### 5.5 清空知识库

```
POST /v1/rag/clear
```

---

## 7. 视觉识别

### 6.1 图片分析

```
POST /v1/vision/analyze
```

**请求体：**

```json
{
    "model": "D:\\models\\Qwen2-VL-2B-Instruct",
    "image_path": "D:\\images\\photo.jpg",
    "prompt": "请详细描述这张图片的内容。",
    "max_tokens": 1024,
    "temperature": 0.7
}
```

需先通过 `POST /v1/models/load`（`model_type: "vision"`）加载视觉模型。

### 6.2 上传图片分析

```
POST /v1/vision/analyze/upload
Content-Type: multipart/form-data
```

| 表单字段     | 类型   | 必填 | 说明                   |
|-------------|--------|------|------------------------|
| `model`     | string | 是   | 视觉模型路径            |
| `prompt`    | string | 否   | 分析提示词              |
| `max_tokens`| int    | 否   | 最大 token 数           |
| `file`      | file   | 是   | 图片文件                |

### 6.3 图片 OCR

```
POST /v1/vision/ocr
Content-Type: multipart/form-data
```

| 表单字段 | 类型   | 必填 | 说明          |
|---------|--------|------|---------------|
| `model` | string | 是   | 视觉模型路径   |
| `file`  | file   | 是   | 图片文件       |

**响应：**

```json
{
    "filename": "receipt.jpg",
    "text": "识别出的文字内容..."
}
```

---

## 8. 健康检查

```
GET /health
```

**响应：**

```json
{
    "status": "ok",
    "loaded_text_models": ["D:\\models\\Qwen2.5-7B-Instruct"],
    "loaded_vision_models": [],
    "rag_documents": 156
}
```

---

## 9. 与 RemoteAssistant 对接

LLM Studio 的 API 完全兼容 RemoteAssistant 的 LLM 配置格式（OpenAI 兼容协议）。

### 配置方式

在 RemoteAssistant 中添加 LLM 模型配置：

| 配置项    | 值                              |
|----------|--------------------------------|
| 类型      | `lmstudio` 或 `custom`         |
| API 地址  | `http://localhost:8000/v1`      |
| User ID   | 在管理后台创建的 User ID         |
| API 密钥  | 对应的 X-API-Key                |
| 模型名称  | 从 `/v1/models` 列表中选择      |

### 连接流程

```
RemoteAssistant                       LLM Studio
    │                                     │
    ├─ GET /v1/models ──────────────────?│  返回可用模型列表
    │  (X-User-ID + X-API-Key)            │
    │                                     │
    ├─ POST /v1/chat/completions ──────?│  自动加载模型 + 推理
    │   (stream: true)                    │
    │?── SSE: data: {"delta":...} ───────┤  流式返回内容
    │?── SSE: data: [DONE] ─────────────┤  流结束
    │                                     │
```

### 兼容性说明

| 特性                        | 状态     | 说明                                |
|----------------------------|----------|-------------------------------------|
| `GET /v1/models`           | ? 兼容  | 返回已下载 + 已加载的全部模型         |
| `POST /v1/chat/completions`| ? 兼容  | 支持 stream/非 stream 两种模式       |
| SSE 流式输出                | ? 兼容  | 标准 `chat.completion.chunk` 格式    |
| 模型自动加载                 | ? 支持  | 首次对话自动加载模型，无需手动操作     |
| `X-User-ID + X-API-Key` 认证 | ? 支持  | 需在管理后台创建用户获取密钥      |
| `Authorization: Bearer` 头  | ? 兼容  | 作为 X-API-Key 的备选传递方式     |
| 管理后台                     | ? 支持  | `/admin` 页面管理用户和密钥       |
| Embeddings 接口             | ? 暂无  | `/v1/embeddings` 未实现              |

---

## 10. 调用示例

### cURL

```bash
# 列出模型
curl -H "X-User-ID: admin" -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/v1/models

# 非流式聊天
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-User-ID: admin" -H "X-API-Key: YOUR_KEY" \
  -d '{
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "什么是机器学习？"}],
    "stream": false
  }'

# 流式聊天
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-User-ID: admin" -H "X-API-Key: YOUR_KEY" \
  -d '{
    "model": "D:\\models\\Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "什么是机器学习？"}],
    "stream": true
  }'
```

### Python

```python
import requests

BASE_URL = "http://localhost:8000"
HEADERS = {
    "X-User-ID": "admin",
    "X-API-Key": "YOUR_KEY",
}

# 非流式调用
resp = requests.post(f"{BASE_URL}/v1/chat/completions",
    headers=HEADERS,
    json={
        "model": "D:\\models\\Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": False,
    },
)
print(resp.json()["choices"][0]["message"]["content"])

# 流式调用
resp = requests.post(f"{BASE_URL}/v1/chat/completions",
    headers=HEADERS,
    json={
        "model": "D:\\models\\Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "讲一个故事"}],
        "stream": True,
    },
    stream=True,
)

for line in resp.iter_lines():
    if line:
        text = line.decode("utf-8")
        if text.startswith("data: ") and text != "data: [DONE]":
            import json
            chunk = json.loads(text[6:])
            content = chunk["choices"][0]["delta"].get("content", "")
            print(content, end="", flush=True)
```

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="YOUR_KEY",
    default_headers={"X-User-ID": "admin"},
)

# 完全兼容 OpenAI SDK
response = client.chat.completions.create(
    model="D:\\models\\Qwen2.5-7B-Instruct",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### JavaScript / Node.js

```javascript
// 流式调用
const response = await fetch("http://localhost:8000/v1/chat/completions", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-User-ID": "admin",
        "X-API-Key": "YOUR_KEY",
    },
    body: JSON.stringify({
        model: "D:\\models\\Qwen2.5-7B-Instruct",
        messages: [{ role: "user", content: "你好" }],
        stream: true,
    }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    for (const line of text.split("\n")) {
        if (line.startsWith("data: ") && line !== "data: [DONE]") {
            const chunk = JSON.parse(line.slice(6));
            process.stdout.write(chunk.choices[0].delta.content || "");
        }
    }
}
```
