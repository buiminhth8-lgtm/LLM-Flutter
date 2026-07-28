# LLM-Studio

## Current Desktop Architecture

LLM-Studio now uses a Flutter Windows desktop client plus a local Python FastAPI backend.
Start the desktop app with:

```powershell
.\scripts\start_desktop.ps1
```

For direct Flutter development:

```powershell
cd apps\flutter_studio
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

The Flutter app starts the backend when `/health` is not already available. The backend is launched from the project root with `.venv\Scripts\python.exe -m llm_studio.cli serve`.

## First-Run Authentication

On first launch, `/v1/setup/status` is public and reports whether local setup is required. If setup is required, Flutter shows an initialization page where the user creates the local administrator password. The backend stores only an Argon2id password hash and returns the first API Key exactly once from `/v1/setup/initialize`.

Flutter persists these desktop settings with `shared_preferences`:

- `llm_studio.api_base_url`
- `llm_studio.user_id`
- `llm_studio.api_key`
- `llm_studio.selected_model_id`

`shared_preferences` is enough for the current local desktop loop, but it is not a high-security key vault on Windows. A future hardening step should move API keys to Windows Credential Manager or `flutter_secure_storage`.

## Unified Model Workflow

Model scanning, listing, loading, unloading, and chat selection now use the unified local model repository rooted at:

```text
models.root_dir: ./data/models
```

The legacy `models_dir: ./models` setting is still accepted for old configuration files, but it is not the chat default when `models.root_dir` is present. Chat requests resolve `model` through `LocalModelRepository`; `model=auto` picks a ready compatible model from the repository and returns `MODEL_NOT_FOUND` when none exists.

Flutter model flow:

1. Open Models.
2. Scan or refresh local models.
3. Load a `ready` model.
4. Chat uses the selected/current model ID instead of always sending `auto`.
5. Unload clears the current model and disables chat until another model is loaded.

## Current Feature Status

Supported:

- First-run setup from Flutter.
- API Key persistence and authenticated API calls.
- Backend stdout/stderr capture with secret redaction.
- Local model scan/list through the unified repository.
- Model load, current model status, unload.
- Non-streaming multi-turn chat bound to the selected loaded model.

Experimental or not complete:

- Full download task UI.
- LoRA merge UI.
- Strict benchmark comparison UI.
- Multi-platform Flutter packaging beyond Windows desktop.
- Installer validation on a clean Windows VM.

## P2 Capability Closure

The backend exposes `GET /v1/capabilities` as the source of truth for feature state. The same table is documented in [docs/CAPABILITIES.md](docs/CAPABILITIES.md).

P2 changes:

- Download jobs now return truthful task state. Unknown totals are returned as `null`; cancel means a cooperative cancellation request, and retry reuses the Hugging Face cache.
- Successful downloads are validated, moved into `data/models`, and then scanned into the unified model repository.
- LoRA scan/load/activate/deactivate/unload are backend-only and use the model adapter API. LoRA Merge is explicitly `not_implemented` and does not modify base models.
- Benchmark jobs are experimental. Loading time, TTFT, and token/s are reported separately, and reports include a local-reference disclaimer.
- Storage cleanup supports preview first and only removes temporary categories such as failed downloads, temporary uploads, old benchmark files, diagnostics packages, and trash. It does not delete formal model weights, external models, LoRA adapters, RAG source documents, or user configuration.
- Diagnostic packages include runtime, version, pip, redacted config, model metadata summaries, disk usage, and capability status. They do not include model weights, full chat logs, RAG document bodies, API keys, tokens, cookies, or password hashes.
- Flutter Windows now shows a minimal Job Center on the Status page for recent backend jobs.

## P3 Flutter Desktop Productization

P3 starts from `master` after P0/P1/P2 integration. The active development branch is:

```text
feat/p3-flutter-desktop-productization
```

Flutter client status:

- `main.dart` is now only the application entry and public export surface.
- `app/` contains MaterialApp, theme, and the desktop shell.
- `core/api/` contains the API client, API exceptions, and SSE parser/client.
- `core/backend/` contains local FastAPI process management and redacted logs.
- `core/config/` persists desktop settings with `shared_preferences`.
- `features/` contains separate Status, Models, Chat, Jobs, Downloads, RAG, Adapters, Benchmark, Storage, Diagnostics, Settings, and Setup surfaces.
- Chat supports non-streaming and SSE streaming generation, Stop Generation, clear history, and regenerate.
- Windows backend settings support local/remote mode, auto-start, restart, stop, and close-on-exit behavior.

Developer scripts:

```powershell
.\scripts\flutter_analyze.ps1
.\scripts\flutter_test.ps1
.\scripts\flutter_build_windows.ps1
.\scripts\flutter_run_windows.ps1
.\scripts\dev_start_all.ps1
```

See [docs/FLUTTER_CLIENT.md](docs/FLUTTER_CLIENT.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md), and [docs/WINDOWS_DESKTOP.md](docs/WINDOWS_DESKTOP.md).

---


> This README is the single source of project documentation. The former `docs/` documents were merged here.

## Flutter Desktop 启动说明

推荐从项目根目录启动桌面端：

```powershell
.\scripts\start_desktop.ps1
```

该脚本会把项目根目录通过 `LLM_STUDIO_ROOT` 传给 Flutter，并由 Flutter Desktop 自动启动本地 FastAPI 后端。

如果需要直接运行 Flutter：

```powershell
cd apps\flutter_studio
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

如果 Python 解释器不在 `.venv\Scripts\python.exe`，请额外指定：

```powershell
flutter run -d windows `
  --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio" `
  --dart-define="LLM_STUDIO_PYTHON=D:\path\to\python.exe"
```

看到 `Missing Python executable` 时，说明项目根目录已经识别成功，但还没有可用于启动后端的 Python 环境。先创建 Python 3.12 虚拟环境并安装依赖：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\scripts\install_windows_cuda.ps1
.\scripts\install_base.ps1
```

## Table of Contents

1. [功能说明](#功能说明)
2. [环境安装说明](#环境安装说明)
3. [RTX5060_RUNTIME_GUIDE](#rtx5060_runtime_guide)
4. [RAG_GUIDE](#rag_guide)
5. [FINETUNE_LOW_VRAM_GUIDE](#finetune_low_vram_guide)
6. [API接口说明](#api接口说明)
7. [API_SECURITY_GUIDE](#api_security_guide)
8. [MODEL_MANAGEMENT_RELEASE_GUIDE](#model_management_release_guide)
9. [编译说明](#编译说明)

---

# 功能说明

## 1. 概述

LLM Studio 是一个**跨平台**的大语言模型（LLM）一站式管理工具，提供模型下载、推理对话、LoRA/QLoRA 微调、**本地文档知识库 (RAG)**、**图像识别**、**REST API 服务**、模型导出与上传等完整工作流。

**支持的操作系统**：Windows / macOS / Linux
**支持的硬件加速**：NVIDIA CUDA GPU · Apple MPS (M1/M2/M3) · CPU

工具同时提供可视化 **Flutter Desktop**（Flutter Desktop）和完整的 **命令行 CLI** 两种使用方式。

---

## 2. 功能模块

### 2.1 模型下载

| 能力 | 说明 |
|------|------|
| 推荐模型一键下载 | 内置 7 个精选模型，覆盖中英文主流模型，选中即下载 |
| 自定义下载 | 输入任意 HuggingFace Repo ID 下载模型 |
| HuggingFace 搜索 | 在线搜索 HuggingFace Hub 模型库，查看下载量与点赞数 |
| 双格式支持 | 支持 **Transformers**（完整权重）和 **GGUF**（量化压缩）两种格式 |
| GGUF 自动检测 | 下载 GGUF 时自动选取 Q4_K_M 量化版本（也可手动指定文件名） |
| 本地模型管理 | 列出、刷新、删除本地已下载模型 |

**内置推荐模型列表**：

| 模型名称 | 大小 | 类型 | 说明 |
|---------|------|------|------|
| Qwen2.5-1.5B-Instruct | 3 GB | Transformers | 通义千问轻量中英文模型 |
| Qwen2.5-7B-Instruct | 15 GB | Transformers | 通义千问中英文模型 |
| Llama-3.1-8B-Instruct | 16 GB | Transformers | Meta Llama 3.1 |
| Mistral-7B-Instruct-v0.3 | 15 GB | Transformers | Mistral AI 高效推理模型 |
| Phi-3-mini-4k-instruct | 7.6 GB | Transformers | 微软 Phi-3 小型高效模型 |
| Qwen2.5-1.5B-Instruct-GGUF | 1 GB | GGUF | Qwen2.5 1.5B Q4_K_M 量化 |
| Llama-3.1-8B-Instruct-GGUF | 4.9 GB | GGUF | Llama 3.1 8B Q4_K_M 量化 |

---

### 2.2 模型推理（对话）

| 能力 | 说明 |
|------|------|
| 双推理引擎 | **TransformersRunner**（HuggingFace 模型）和 **GGUFRunner**（llama-cpp-python） |
| 自动引擎选择 | 根据模型文件后缀自动选用对应引擎 |
| 流式输出 | 逐 token 实时输出，用户无需等待完整生成 |
| 聊天模板 | 自动应用模型的 chat_template 格式化对话 |
| 4-bit 量化推理 | CUDA 环境下自动启用 BitsAndBytes NF4 量化，降低显存占用 |
| 动态加载/卸载 | 按需加载模型，用完卸载释放内存/显存 |

**可调参数**：

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| Temperature | 0.7 | 0 ~ 2 | 采样温度，越高越随机 |
| Max Tokens | 2048 | 64 ~ 4096 | 最大生成 token 数 |
| Top P | 0.9 | 0 ~ 1 | Nucleus 采样阈值 |
| Top K | 40 | — | Top-K 采样 |
| Repeat Penalty | 1.1 | — | 重复惩罚系数 |
| Context Length | 4096 | — | 上下文窗口长度（GGUF） |

---

### 2.3 模型微调

支持 **LoRA** 和 **QLoRA** 两种参数高效微调方法。

| 能力 | 说明 |
|------|------|
| LoRA 微调 | 冻结基座模型大部分参数，仅训练低秩适配矩阵，显存友好 |
| QLoRA 微调 | 在 LoRA 基础上对基座模型做 4-bit NF4 量化加载，进一步降低显存 |
| 多格式数据集 | 支持 **Alpaca 格式** 和 **ShareGPT 格式** |
| 实时训练进度 | Flutter Desktop 和 CLI 均提供 step/loss/lr 实时反馈 |
| 断点保存 | 每 N 步自动保存 checkpoint，最多保留 3 个 |
| 模型合并 | 训练完成后可将 LoRA 权重合并回基座模型 |

**微调超参数**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| LoRA Rank (r) | 16 | 低秩矩阵的秩，越大拟合能力越强 |
| LoRA Alpha | 32 | 缩放系数 |
| LoRA Dropout | 0.05 | Dropout 防过拟合 |
| Target Modules | q_proj, v_proj, k_proj, o_proj | 作用的注意力层 |
| Learning Rate | 2e-4 | 学习率 |
| Epochs | 3 | 训练轮数 |
| Batch Size | 4 | 每设备批大小 |
| Gradient Accumulation | 4 | 梯度累积步数，等效 batch = 16 |
| Max Sequence Length | 512 | 训练最大序列长度 |
| Warmup Ratio | 0.03 | 预热比例 |
| FP16 | true | 混合精度训练 |

**支持的数据集格式**：

#### Alpaca 格式 (.jsonl)
```json
{"instruction": "翻译以下句子为英文", "input": "今天天气真好", "output": "The weather is really nice today."}
{"instruction": "写一首诗", "input": "", "output": "春风拂面来，花开满园栽。"}
```

#### ShareGPT 格式 (.jsonl)
```json
{"conversations": [{"from": "human", "value": "你好"}, {"from": "gpt", "value": "你好！有什么可以帮助你？"}]}
{"conversations": [{"from": "system", "value": "你是一个助手"}, {"from": "human", "value": "介绍自己"}, {"from": "gpt", "value": "我是 AI 助手。"}]}
```

---

### 2.4 模型导出与上传

| 能力 | 说明 |
|------|------|
| 本地保存副本 | 把微调后的模型复制到指定目录 |
| 上传 HuggingFace | 一键将模型上传到 HuggingFace Hub，支持私有/公开仓库 |
| GGUF 转换 | 将 Transformers 格式模型转为 GGUF 量化格式（需 llama.cpp 支持） |

---

### 2.5 本地文档知识库 (RAG)

**RAG（Retrieval-Augmented Generation）** 检索增强生成，让大模型基于你的本地文档内容进行回答。

| 能力 | 说明 |
|------|------|
| 多格式文档解析 | 支持 PDF、Word (.docx)、Excel (.xlsx/.xls)、CSV、TXT、Markdown、HTML、PowerPoint (.pptx)、EPUB、JSON/JSONL |
| 文件上传投喂 | Flutter Desktop拖拽上传多个文件，一键导入知识库 |
| 目录批量投喂 | 指定本地目录，递归扫描所有支持的文件自动导入 |
| 智能分块 | 文档自动按段落/句子分块，支持配置 chunk_size 和 overlap |
| 向量化存储 | 使用 sentence-transformers 嵌入模型（默认 BAAI/bge-small-zh-v1.5）生成文档向量 |
| 相似度检索 | 输入问题时自动检索最相关的文档片段 |
| RAG 增强问答 | 将检索到的文档片段作为上下文注入 prompt，大幅提升回答准确性 |
| 知识库持久化 | 向量库保存到本地磁盘，重启后自动加载 |
| 来源追溯 | 回答时显示参考文档片段及来源文件名和相关度分数 |

**支持的文档格式**：

| 格式 | 扩展名 | 解析库 |
|------|--------|--------|
| PDF | .pdf | PyMuPDF / pdfminer |
| Word | .docx | python-docx |
| Excel | .xlsx / .xls | openpyxl |
| CSV | .csv | 内置 csv |
| 纯文本 | .txt | 内置 |
| Markdown | .md | 内置 |
| HTML | .html / .htm | BeautifulSoup |
| PowerPoint | .pptx | python-pptx |
| EPUB | .epub | ebooklib |
| JSON | .json / .jsonl | 内置 json |

---

### 2.6 图像识别

支持加载视觉语言模型（Vision-Language Model），实现图片内容理解和 OCR 文字提取。

| 能力 | 说明 |
|------|------|
| 图片内容描述 | 上传图片，AI 自动描述图中内容 |
| 图片问答 | 针对图片内容提出特定问题 |
| OCR 文字识别 | 从图片中提取所有文字（支持中英文） |
| 多格式支持 | JPG / JPEG / PNG / BMP / GIF / WebP / TIFF |
| 多 OCR 后端 | 优先 PaddleOCR → EasyOCR → 视觉模型兜底 |

**推荐视觉模型**：

| 模型 | 大小 | 说明 |
|------|------|------|
| Qwen2-VL-2B-Instruct | 4.5 GB | 轻量图文理解模型 |
| Qwen2-VL-7B-Instruct | 16 GB | 强大的图文理解模型 |

---

### 2.7 REST API 服务

内置 **FastAPI** REST API 服务器，兼容 **OpenAI Chat Completions** 格式，第三方程序可通过 HTTP 接口调用本地模型。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查，返回已加载模型和知识库状态 |
| `/v1/models` | GET | 列出所有已加载的文本和视觉模型 |
| `/v1/models/load` | POST | 加载模型（文本或视觉） |
| `/v1/models/unload` | POST | 卸载模型释放内存 |
| `/v1/chat/completions` | POST | **OpenAI 兼容聊天接口**（支持 SSE 流式） |
| `/v1/rag/ingest` | POST | 投喂本地文件/目录到知识库 |
| `/v1/rag/ingest/upload` | POST | 上传文件到知识库 |
| `/v1/rag/query` | POST | RAG 知识库问答（检索 + 生成） |
| `/v1/rag/status` | GET | 查看知识库状态 |
| `/v1/rag/clear` | POST | 清空知识库 |
| `/v1/vision/analyze` | POST | 图片分析（指定本地路径） |
| `/v1/vision/analyze/upload` | POST | 上传图片分析 |
| `/v1/vision/ocr` | POST | 图片 OCR 文字识别 |
| `/admin/api/*` | — | 内部管理 API（用户 CRUD、密钥管理；供 Flutter 管理页复用） |

**认证方式**：`X-User-ID` + `X-API-Key` 请求头（在管理后台中创建用户后获取）。

启动 API 服务：

```bash
llm-studio serve                 # 默认端口 8000
llm-studio serve --port 9000     # 自定义端口
```

API 文档（Swagger UI）自动生成：`http://localhost:8000/docs`

**调用示例**：

```python
import requests
API = "http://localhost:8000"
HEADERS = {"X-User-ID": "admin", "X-API-Key": "你的API密钥"}

# 加载模型
requests.post(f"{API}/v1/models/load", json={
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct"
}, headers=HEADERS)

# Chat completion (OpenAI compatible)
resp = requests.post(f"{API}/v1/chat/completions", json={
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "hello"}],
    "temperature": 0.7
}, headers=HEADERS)
print(resp.json()["choices"][0]["message"]["content"])

# 投喂文档
requests.post(f"{API}/v1/rag/ingest",
    json={"file_path": "C:/docs/manual.pdf"}, headers=HEADERS)

# RAG 问答
resp = requests.post(f"{API}/v1/rag/query", json={
    "question": "产品有哪些功能？",
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct"
}, headers=HEADERS)
print(resp.json()["answer"])
```

---

### 2.8 Flutter Desktop API Key Management

API users and keys are managed through Flutter Desktop calling local management APIs.


#### 登录

- 不再提供硬编码默认管理员密码；首次启动读取 `LLM_STUDIO_INITIAL_ADMIN_PASSWORD`，未设置时生成一次性随机初始密码并只在启动日志显示。
- 首次启动自动创建默认 `admin` 用户和随机 API Key
- 用户数据持久化存储在 `data/api_users.json`，重启服务不丢失

#### 功能列表

| 功能 | 说明 |
|------|------|
| 新建用户 | 输入 User ID，系统自动生成安全随机 API Key（`sk-llmstudio-` 前缀 + 40位hex） |
| 查看密钥 | 展示完整的 X-User-ID 和 X-API-Key，附带 cURL 调用示例，一键复制 |
| 重置密钥 | 重新生成 API Key，原 Key 立即失效 |
| 启用 / 禁用 | 临时禁用用户（不删除），适合暂停某个客户端的访问权限 |
| 删除用户 | 永久删除用户及其 Key |
| 修改密码 | 修改管理后台的登录密码 |
| 用户统计 | 首页展示用户总数、启用数、管理员数 |

#### 密钥使用方式

在管理后台创建用户后，将生成的凭证添加到 API 请求头：

```
X-User-ID: your_user_id
X-API-Key: sk-llmstudio-xxxxxxxxxxxx
```

也支持标准的 `Authorization: Bearer` 作为 API Key 的备选传递方式（仍需 `X-User-ID` 头）。

#### 管理后台 API

管理后台本身也提供 REST API，可用于自动化管理：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/admin/api/login` | POST | 管理员登录 |
| `/admin/api/logout` | POST | 退出登录 |
| `/admin/api/users` | GET | 列出所有用户 |
| `/admin/api/users` | POST | 创建新用户 |
| `/admin/api/users/{id}` | PUT | 更新用户信息 |
| `/admin/api/users/{id}` | DELETE | 删除用户 |
| `/admin/api/users/{id}/toggle` | POST | 启用/禁用用户 |
| `/admin/api/users/{id}/regenerate` | POST | 重新生成 API Key |
| `/admin/api/users/{id}/key` | GET | 获取完整 API Key |
| `/admin/api/change-password` | POST | 修改管理员密码 |

---

### 2.9 Web 可视化界面

基于 **Flutter Desktop** 构建，浏览器访问，共 8 个功能页签：

| 页签 | 功能 |
|------|------|
| ? 模型下载 | 推荐模型选择下载、自定义下载、搜索 HuggingFace、查看本地模型 |
| ? 模型推理 | 加载/卸载模型、参数调节滑块、流式对话窗口 |
| ? 模型微调 | 选择基座模型、上传数据集、配置超参数、一键微调并查看训练日志 |
| ? 知识库 (RAG) | 文档上传投喂、目录批量导入、知识库问答、参考来源展示 |
| ?? 图像识别 | 加载视觉模型、图片分析问答、OCR 文字识别 |
| ? 模型导出/上传 | 选择微调模型、上传 HuggingFace（支持 Token 和私有仓库）、另存副本 |
| ? API 服务 | API 启动说明、完整端点文档、Python/cURL 调用示例 |
| ?? 系统信息 | 显示操作系统、CPU/RAM、GPU 型号/显存、推理设备 |

启动命令：

```bash
scripts/start_desktop.ps1                  # starts Flutter Desktop and local FastAPI service
LLM_STUDIO_ROOT=<repo> scripts/start_desktop.ps1  # override repository root when needed
```

---

### 2.10 命令行工具 (CLI)

CLI 基于 **Click** 框架，使用 **Rich** 美化输出，提供完整的终端操作能力。

```
llm-studio
├── info                           # 显示系统硬件信息
├── model                          # 模型管理
│   ├── list                       # 列出本地模型
│   ├── registry                   # 显示推荐模型列表
│   ├── download <名称或Repo>       # 下载模型
│   ├── search <关键词>             # 搜索 HuggingFace
│   └── delete <路径>               # 删除本地模型
├── chat <模型路径>                  # 交互式对话
├── finetune <模型> <数据集>         # 微调训练
├── rag                             # 知识库管理
│   ├── ingest <文件或目录>          # 投喂文档
│   ├── status                     # 查看知识库状态
│   ├── query <问题>                # 检索知识库
│   └── clear                      # 清空知识库
├── upload <模型路径> <Repo ID>      # 上传到 HuggingFace
├── serve                           # 启动 REST API 服务
└── serve                           # 启动本地 FastAPI 服务
```

---

### 2.11 系统检测与自适应

程序启动时自动检测运行环境并选择最优配置：

| 检测项 | 自适应行为 |
|--------|-----------|
| NVIDIA CUDA GPU | 启用 GPU 加速推理 + 4-bit 量化加载 |
| Apple MPS (M 系列芯片) | 启用 MPS 后端加速 |
| 仅 CPU | 回退到 CPU 推理（float32） |
| 可用内存/显存 | 展示可用资源帮助用户选择合适大小的模型 |

---

## 3. 配置文件

所有默认参数集中在 `config.yaml` 中管理：

- `models_dir` — 模型存放目录
- `finetune_output_dir` — 微调输出目录
- `datasets_dir` — 数据集目录
- `inference` — 推理参数（temperature、max_tokens 等）
- `finetune` — 微调参数（LoRA 配置、学习率等）
- `rag` — RAG 设置（嵌入模型、分块大小、检索 Top-K、Prompt 模板）
- `auth` — 认证开关（`enabled: true` 启用，用户通过管理后台管理）
- `api` — API 服务设置（端口等）
- `model_registry` — 推荐文本模型列表
- `vision_model_registry` — 推荐视觉模型列表

路径支持相对路径（相对于 config.yaml 所在目录）和绝对路径，目录不存在时自动创建。

---

## 4. 典型使用流程

### 基本流程
```
1. 安装环境 → 2. 下载模型 → 3. 对话测试 → 4. 准备数据集 → 5. 微调 → 6. 测试微调模型 → 7. 导出/上传
```

### 知识库问答流程
```
1. 下载模型 → 2. 投喂本地文档 → 3. 基于知识库问答
```

### API 服务流程
```
1. 下载模型 → 2. 启动 API 服务 → 3. 访问管理后台创建用户 → 4. 分发 X-User-ID + X-API-Key → 5. 第三方程序通过 HTTP 调用
```

**示例**：

```bash
# 安装

# 下载一个轻量模型
llm-studio model download "Qwen2.5-1.5B-Instruct"

# 对话测试
llm-studio chat ./models/Qwen--Qwen2.5-1.5B-Instruct

# 投喂本地文档到知识库
llm-studio rag ingest ./my_documents/
llm-studio rag ingest ./report.pdf
llm-studio rag status

# 知识库检索
llm-studio rag query "产品的主要功能有哪些？"

# 用自己的数据微调
llm-studio finetune ./models/Qwen--Qwen2.5-1.5B-Instruct ./datasets/my_data.jsonl \
    --method lora --epochs 3 --lr 2e-4

# 上传到 HuggingFace
llm-studio upload ./finetuned_models/cli_finetune/final myname/my-custom-model --private

# 启动 API 服务供第三方调用
llm-studio serve --port 8000

# 启动 Flutter Desktop（包含所有功能）
scripts/start_desktop.ps1
```

---

# 环境安装说明

## 1. 系统要求

### 1.1 操作系统

| 操作系统 | 最低版本 | 说明 |
|---------|---------|------|
| Windows | 10 (64-bit) | 推荐 Windows 10/11 |
| macOS | 12.3+ (Monterey) | Apple MPS 加速需 macOS 12.3+ |
| Linux | Ubuntu 20.04+ / CentOS 8+ | 其他发行版也可，需有 Python 3.9+ |

### 1.2 硬件要求

| 项目 | 最低配置 | 推荐配置 | 说明 |
|------|---------|---------|------|
| CPU | 4 核 | 8 核+ | 影响数据预处理和 CPU 推理速度 |
| 内存 | 8 GB | 16 GB+ | 加载 7B 模型至少需 16 GB |
| 磁盘 | 10 GB 空闲 | 50 GB+ | 视下载模型大小，7B 模型约 15 GB |
| GPU (可选) | NVIDIA 6 GB VRAM | NVIDIA 8 GB+ VRAM | 大幅加速推理和微调 |

> **不同模型对硬件的要求参考**：
>
> | 模型大小 | 最低 RAM (CPU) | 最低 VRAM (GPU) |
> |---------|---------------|----------------|
> | 1.5B (GGUF Q4) | 4 GB | 2 GB |
> | 1.5B | 8 GB | 4 GB |
> | 7B (GGUF Q4) | 8 GB | 4 GB |
> | 7B | 16 GB | 8 GB |
> | 7B 微调 (LoRA) | 16 GB | 8 GB |
> | 7B 微调 (QLoRA) | 12 GB | 6 GB |

### 1.3 软件前置依赖

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9 ~ 3.12 | **必须** |
| pip | 最新版 | 随 Python 安装 |
| Git | 2.x+ | 从 HuggingFace Hub 下载大模型时需要 |
| CUDA Toolkit | 11.8+ 或 12.x | 仅 NVIDIA GPU 用户需要 |
| C++ 编译器 | — | 部分依赖包编译需要（见下文） |

---

## 2. Python 安装

### 2.1 Windows

1. 从 [python.org](https://www.python.org/downloads/) 下载 Python 3.10+ 安装包
2. 安装时 **务必勾选** "Add Python to PATH"
3. 验证安装：
   ```powershell
   python --version    # 应显示 Python 3.10.x 或更高
   pip --version
   ```

### 2.2 macOS

```bash
# 使用 Homebrew 安装
brew install python@3.10

# 验证
python3 --version
```

### 2.3 Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-dev

# 验证
python3 --version
```

### 2.4 Linux (CentOS/RHEL)

```bash
sudo dnf install python3 python3-devel python3-pip
```

---

## 3. GPU 环境配置（可选）

### 3.1 NVIDIA GPU (Windows / Linux)

1. **确认 GPU 型号和驱动**：
   ```bash
   nvidia-smi
   ```
   输出中应包含驱动版本和 CUDA 版本信息。

2. **安装 CUDA Toolkit**：
   - 前往 [NVIDIA CUDA 下载页](https://developer.nvidia.com/cuda-toolkit-archive)
   - 推荐安装 CUDA 12.1 或 CUDA 11.8
   - 安装后验证：
     ```bash
     nvcc --version
     ```

3. **安装 GPU 版 PyTorch**（在项目环境中）：
   ```bash
   # CUDA 12.1
   pip install torch --index-url https://download.pytorch.org/whl/cu121

   # CUDA 11.8
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

4. **验证 CUDA 可用**：
   ```python
   python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
   ```

### 3.2 Apple MPS (macOS M1/M2/M3)

- macOS 12.3 以上版本自动支持，无需额外安装
- 安装 PyTorch 后验证：
  ```python
  python -c "import torch; print(torch.backends.mps.is_available())"
  ```

### 3.3 仅 CPU

无需额外配置，正常安装 PyTorch 即可，程序会自动回退到 CPU 运行。

---

## 4. 项目安装

### 4.1 一键安装（推荐）

#### Windows

```powershell
cd LLM-Studio
```

脚本会自动完成：创建虚拟环境 → 安装依赖 → 注册 `llm-studio` 命令。

#### macOS / Linux

```bash
cd LLM-Studio
.\scripts\setup_windows_python312.ps1
.\scripts\install_base.ps1
```

### 4.2 手动安装

#### 步骤 1：创建虚拟环境

```bash
cd LLM-Studio

# 创建
python -m venv venv

# 激活
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate
```

> 激活后命令行前缀会出现 `(venv)` 标记。

#### 步骤 2：升级 pip

```bash
pip install --upgrade pip
```

#### 步骤 3：安装 PyTorch

根据你的硬件选择对应版本：

```bash
# --- CPU Only ---
pip install torch torchvision torchaudio

# --- NVIDIA GPU (CUDA 12.1) ---
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# --- NVIDIA GPU (CUDA 11.8) ---
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# --- macOS (MPS 自动启用) ---
pip install torch torchvision torchaudio
```

#### 步骤 4：安装项目依赖

```bash
pip install -r requirements.txt
```

#### 步骤 5：安装项目为命令行工具

```bash
pip install -e .
```

安装后即可在终端使用 `llm-studio` 命令。

---

## 5. 依赖包说明

### 5.1 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| torch | >=2.1.0 | PyTorch 深度学习框架 |
| transformers | >=4.38.0 | HuggingFace Transformers 模型库 |
| huggingface_hub | >=0.20.0 | HuggingFace Hub API（下载/上传） |
| accelerate | >=0.26.0 | 模型加速和多设备调度 |
| safetensors | >=0.4.0 | 安全的模型权重序列化格式 |

### 5.2 量化与推理

| 包名 | 版本 | 用途 |
|------|------|------|
| bitsandbytes | >=0.42.0 | 4/8-bit 模型量化（QLoRA 必需） |
| llama-cpp-python | >=0.2.50 | GGUF 格式模型推理引擎 |
| gptqmodel | >=2,<4 | 可选 GPTQ 量化支持 |

### 5.3 微调

| 包名 | 版本 | 用途 |
|------|------|------|
| peft | >=0.8.0 | LoRA / QLoRA 实现 |
| trl | >=0.7.0 | 训练工具箱 |
| datasets | >=2.17.0 | HuggingFace 数据集处理 |

### 5.4 文档解析（RAG）

| 包名 | 版本 | 用途 |
|------|------|------|
| pymupdf | >=1.23.0 | PDF 文件解析 |
| python-docx | >=1.1.0 | Word (.docx) 文件解析 |
| openpyxl | >=3.1.0 | Excel (.xlsx/.xls) 文件解析 |
| beautifulsoup4 | >=4.12.0 | HTML 文件解析 |
| python-pptx | >=0.6.23 | PowerPoint (.pptx) 解析 |
| sentence-transformers | >=2.3.0 | 文本向量化嵌入模型 |
| numpy | >=1.24.0 | 向量计算 |

### 5.5 图像识别

| 包名 | 版本 | 用途 |
|------|------|------|
| Pillow | >=10.0.0 | 图像处理 |
| paddleocr | — | (可选) OCR 文字识别（中文优秀） |
| easyocr | — | (可选) OCR 文字识别备选 |

### 5.6 API 服务

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.109.0 | REST API 框架 |
| uvicorn | >=0.27.0 | ASGI 服务器 |
| python-multipart | >=0.0.6 | 文件上传支持 |

### 5.7 界面与工具

| 包名 | 版本 | 用途 |
|------|------|------|
| flutter | >=4.15.0 | Web 可视化界面 |
| rich | >=13.7.0 | CLI 美化输出 |
| click | >=8.1.0 | CLI 命令框架 |
| typer | >=0.9.0 | CLI 补充工具 |
| psutil | >=5.9.0 | 获取系统硬件信息 |
| pyyaml | >=6.0.0 | YAML 配置文件解析 |
| tqdm | >=4.66.0 | 进度条 |
| requests | >=2.31.0 | HTTP 请求 |

---

## 6. 特殊依赖安装说明

### 6.1 bitsandbytes (Windows)

Windows 下 bitsandbytes 曾有兼容性问题，当前已原生支持：

```bash
pip install bitsandbytes
```

如遇安装失败，可尝试：
```bash
pip install bitsandbytes-windows
```

> 该包仅支持 NVIDIA CUDA GPU。CPU 或 macOS 环境不需要安装此包，程序会自动跳过量化功能。

### 6.2 llama-cpp-python (GPU 加速)

默认 pip 安装的是 CPU 版本。若需 GPU 加速：

```bash
# NVIDIA GPU (CUDA)
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Apple MPS
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Windows 下需安装 [CMake](https://cmake.org/download/) 和 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)（勾选 "C++ 桌面开发" 工作负载）。

### 6.3 GPTQModel（可选）

如安装过程报错 C++ 编译器缺失：

- **Windows**：安装 Visual Studio Build Tools
- **Linux**：`sudo apt install build-essential`
- **macOS**：`xcode-select --install`

---

## 7. HuggingFace 账号配置（可选）

从 HuggingFace 下载部分受限模型或上传模型时需要账号及 Token：

1. 注册 [HuggingFace 账号](https://huggingface.co/join)
2. 创建 Access Token：进入 [Settings → Access Tokens](https://huggingface.co/settings/tokens) → New Token → 选择 `write` 权限
3. 配置本地登录：
   ```bash
   pip install huggingface_hub
   huggingface-cli login
   # 粘贴你的 Token
   ```

登录状态会缓存在本地，后续无需重复输入。

---

## 8. 网络与镜像配置（中国大陆用户）

如 HuggingFace 下载速度慢，可配置镜像：

```bash
# 设置 HuggingFace 镜像（推荐 hf-mirror.com）
# Windows PowerShell:
$env:HF_ENDPOINT = "https://hf-mirror.com"

# Linux / macOS:
export HF_ENDPOINT="https://hf-mirror.com"

# 写入配置文件使其永久生效
# Windows: 在系统环境变量中添加 HF_ENDPOINT = https://hf-mirror.com
# Linux/macOS: 添加到 ~/.bashrc 或 ~/.zshrc
```

pip 镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 9. 验证安装

安装完成后执行以下命令验证环境是否正常：

```bash
# 1. 检查命令行工具
llm-studio --help

# 2. 查看系统检测信息
llm-studio info

# 3. 查看推荐模型
llm-studio model registry

# 4. 启动 Flutter Desktop（包含所有功能）
scripts/start_desktop.ps1

# 5. 启动 API 服务
llm-studio serve
```

如果 `llm-studio info` 输出包含正确的操作系统、内存和 GPU 信息，说明安装成功。

---

## 10. 常见安装问题

| 问题 | 解决方案 |
|------|---------|
| `python` 命令找不到 | Windows: 重新安装并勾选 "Add to PATH"；Linux: 使用 `python3` |
| `pip install torch` 非常慢 | 使用 pip 镜像或手动从 [PyTorch 官网](https://pytorch.org/) 选版本安装 |
| `bitsandbytes` 安装失败 | CPU 环境可忽略此包；GPU 环境确认已安装 CUDA |
| `llama-cpp-python` 编译失败 | 安装 CMake 和 C++ 编译器；或使用预编译 wheel |
| `CUDA out of memory` | 使用更小的模型或 GGUF 量化模型，或启用 QLoRA 量化加载 |
| `llm-studio` 命令不存在 | 确认已 `pip install -e .` 且虚拟环境已激活 |
| HuggingFace 下载超时 | 配置 HF_ENDPOINT 镜像（见第 8 节） |
AutoGPTQ 已从默认依赖移除。需要 GPTQ 模型时安装：

```powershell
pip install -r requirements/cuda.txt
```

未安装 GPTQModel 不应影响基础 Transformers/GGUF 推理启动。

---

# RTX5060_RUNTIME_GUIDE

Recommended environment:

- Windows 11 x64
- Python 3.12 x64
- CUDA PyTorch installed with `scripts/install_windows_cuda.ps1`
- `trust_remote_code: false`

Run diagnostics:

```powershell
python -m llm_studio.runtime.diagnostics
python -m llm_studio.cli doctor
```

Default runtime policy:

- 1B-3B Transformers models: BF16 when supported, otherwise FP16.
- 7B/8B models: prefer 4-bit if bitsandbytes probe passes, otherwise BF16/FP16 with offload or GGUF.
- 14B and larger: not loaded as full GPU models by default on 8GB VRAM.
- `attention_backend: sdpa` on CUDA unless a model requires fallback.
- `max_gpu_memory: 7GiB` reserves roughly 1GiB for runtime headroom.

Concurrency:

- GPU inference concurrency defaults to `1`.
- Queue limit defaults to `8`.
- Queue full returns `QUEUE_FULL`.

Manual validation should record model name, dtype, quantization, attention backend, peak VRAM, first token latency, and tokens/sec. Do not report GPU validation as passed unless it was run on the target machine.

---

# RAG_GUIDE

RAG settings live in `config.yaml`:

```yaml
rag:
  embedding_model: BAAI/bge-small-zh-v1.5
  device: cpu
  chunk_size: 500
  chunk_overlap: 50
  top_k: 5
  index_path: ./data/rag
```

On RTX 5060 Laptop 8GB, embeddings default to CPU so the main model keeps GPU memory.

Chunking order:

1. Paragraph boundaries.
2. Chinese and English sentence punctuation.
3. Fixed length fallback with overlap.

The index stores:

- `schema_version`
- `embedding_model`
- `embedding_dimension`
- `created_at`
- document and chunk counts

Loading refuses incompatible model or dimension metadata and asks for rebuild instead of returning incorrect retrieval results.

---

# FINETUNE_LOW_VRAM_GUIDE

RTX 5060 Laptop 8GB defaults:

```yaml
finetune:
  method: qlora
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 16
  max_seq_length: 1024
  gradient_checkpointing: true
  precision: auto
  target_modules: all-linear
```

Training data uses dynamic padding. Padding, system messages, and user prompts are masked with `-100`; assistant replies are supervised.

Risk levels:

- 1B-3B QLoRA: allowed for short validation.
- 7B/8B QLoRA: high risk on 8GB; use batch size 1 and short runs only.
- 14B+: unsupported by default on 8GB VRAM.

QLoRA dependency failures are not silently converted into full-precision training. Install CUDA optional dependencies first:

```powershell
.\scripts\install_optional_cuda.ps1
```

---

# API接口说明

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

> 用户管理由 Flutter Desktop 通过本地管理 API 完成，无需手动编辑配置文件。

### 2.1 管理后台

启动 API 服务后，访问管理后台创建和管理 API 用户：

```
Flutter Desktop 设置页
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
| `/admin/api/*`    | 内部管理 API    |

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
| 管理     | POST   | `/admin/api/login`         | 管理 API 登录          |
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
| Flutter 管理页                | 支持    | 通过本地管理 API 管理用户和密钥     |
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

---

# API_SECURITY_GUIDE

Security defaults:

- `trust_remote_code: false`
- API host defaults to `127.0.0.1`
- CORS uses explicit `api.allowed_origins`
- `allow_origins=["*"]` with credentials is rejected
- Admin password is stored as Argon2id
- API keys are stored as SHA-256 hashes
- Full API keys are returned only on creation or regeneration

Set the first admin password:

```powershell
$env:LLM_STUDIO_INITIAL_ADMIN_PASSWORD = "use-a-long-random-password"
python -m llm_studio.cli serve
```

Do not log Authorization headers, cookies, passwords, or full API keys. Use `redact_secret()` for diagnostics.

---

# MODEL_MANAGEMENT_RELEASE_GUIDE

第三阶段新增本地模型仓库、后台任务、LoRA 管理、Benchmark、存储治理和诊断包导出。

## Model Repository

- 扫描 `data/models/transformers`、`data/models/gguf`、`data/models/gptq`、`data/models/awq`。
- 扫描只读取 `config.json`、量化配置、文件名和 GGUF header，不加载权重。
- 扫描阶段不调用 `AutoModel.from_pretrained`，也不启用 `trust_remote_code`。
- 单个模型损坏会记录 `metadata_errors`，不会中断整个列表。

## Downloads

- 下载通过后台 `MODEL_DOWNLOAD` Job 执行。
- Hugging Face Token 只来自环境变量或请求内存对象，不写入 Job payload。
- 下载先进入 `data/downloads`，校验通过后才移动到正式模型目录。
- 取消后重新开始会利用 Hugging Face 缓存自动续传；UI 不伪装成真正暂停。

## LoRA

- Adapter 扫描读取 `adapter_config.json` 和 adapter 权重文件。
- 推理侧使用 PEFT 官方接口 `load_adapter`、`set_adapter`、`disable_adapter`、`delete_adapter`。
- 合并任务会生成新模型目录，不覆盖原始基础模型。

## Benchmark

- Benchmark 逐个模型加载、测试、卸载。
- 指标区分加载时间、TTFT、生成耗时和 Token/s。
- 默认 warmup=1、measured=3、max_new_tokens=128、context=[512, 2048]，不默认跑超长上下文。

## Diagnostics

诊断包包含运行时、版本、pip freeze、脱敏配置、模型摘要和磁盘摘要。不包含模型权重、聊天记录、文档正文、Token、Cookie 或密码。

## Windows Release

当前推荐便携目录版。PyInstaller 和 Inno Setup 文件是可复现脚手架，必须在干净 Windows 用户环境验证后再发布。

---

# 编译说明

## 1. 项目构建概述

LLM Studio 是一个纯 Python 项目，**无需传统意义上的编译**。所谓"编译"即为以下几种场景：

- **开发模式安装**（pip install -e .）— 最常用
- **构建发行包**（sdist / wheel）— 分发给他人
- **打包为可执行程序**（PyInstaller / cx_Freeze）— 免 Python 环境独立运行

---

## 2. 开发模式安装（推荐）

开发时使用 editable 安装，代码修改即时生效：

```bash
cd LLM-Studio

# 创建并激活虚拟环境
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 可编辑模式安装
pip install -e .
```

安装完成后，`llm-studio` 命令全局可用：

```bash
llm-studio --help
llm-studio info
scripts/start_desktop.ps1
llm-studio serve
```

---

## 3. 构建发行包

### 3.1 构建 sdist + wheel

```bash
# 安装构建工具
pip install build

# 构建
python -m build
```

输出在 `dist/` 目录下：
```
dist/
├── llm_studio-1.0.0.tar.gz        # 源码包 (sdist)
└── llm_studio-1.0.0-py3-none-any.whl   # wheel 包
```

### 3.2 安装 wheel 包

```bash
pip install dist/llm_studio-1.0.0-py3-none-any.whl
```

### 3.3 上传到 PyPI（可选）

```bash
pip install twine
twine upload dist/*
```

---

## 4. 打包为独立可执行程序（免 Python 环境）

### 4.1 使用 PyInstaller（Windows / macOS / Linux）

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包 CLI 工具
pyinstaller --name llm-studio \
    --onedir \
    --hidden-import=llm_studio \
    --hidden-import=llm_studio.cli \
    --hidden-import=llm_studio.config \
    --hidden-import=llm_studio.downloader \
    --hidden-import=llm_studio.runner \
    --hidden-import=llm_studio.finetuner \
    --hidden-import=llm_studio.exporter \
    --hidden-import=llm_studio.rag \
    --hidden-import=llm_studio.vision \
    --hidden-import=llm_studio.document_loader \
    --hidden-import=llm_studio.api_server \
    --hidden-import=llm_studio.api_server \
    --collect-all fastapi \
    --collect-all transformers \
    --collect-all sentence_transformers \
    --add-data "config.yaml;." \
    llm_studio/cli.py
```

> **注意**：由于 PyTorch、Transformers 等库体积较大，打包后的目录可能超过 2 GB。
> 建议使用 `--onedir` 模式而非 `--onefile`，以便后续更新模型文件。

打包输出在 `dist/llm-studio/` 目录下。

### 4.2 Windows 打包脚本

创建 `build.bat`:

```batch
@echo off
echo 打包 LLM Studio...

pip install pyinstaller

pyinstaller --name llm-studio ^
    --onedir ^
    --hidden-import=llm_studio ^
    --hidden-import=llm_studio.cli ^
    --hidden-import=llm_studio.config ^
    --hidden-import=llm_studio.downloader ^
    --hidden-import=llm_studio.runner ^
    --hidden-import=llm_studio.finetuner ^
    --hidden-import=llm_studio.exporter ^
    --hidden-import=llm_studio.rag ^
    --hidden-import=llm_studio.vision ^
    --hidden-import=llm_studio.document_loader ^
    --hidden-import=llm_studio.api_server ^
    --hidden-import=llm_studio.api_server ^
    --collect-all fastapi ^
    --collect-all transformers ^
    --add-data "config.yaml;." ^
    llm_studio/cli.py

echo 打包完成！输出目录: dist\llm-studio\
pause
```

---

## 5. 各模块依赖编译说明

部分 Python 依赖包含 C/C++ 扩展，需要编译环境。以下说明各平台的编译工具需求：

### 5.1 Windows

**需安装 Visual Studio Build Tools**：

1. 下载 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 安装时勾选 **"使用 C++ 的桌面开发"** 工作负载
3. 确保包含 **Windows SDK** 和 **MSVC 编译器**

涉及编译的依赖包：
| 包 | 需要编译 | 说明 |
|---|---------|------|
| bitsandbytes | 否（提供预编译 wheel） | 仅 CUDA 环境 |
| llama-cpp-python | 视情况 | CPU 版有预编译 wheel；GPU 版需 CMake + CUDA |
| gptqmodel | 可选 | GPTQ 后端，不作为基础依赖 |
| pymupdf | 否 | 提供预编译 wheel |
| sentence-transformers | 否 | 纯 Python |

**llama-cpp-python GPU 版编译**：

```bash
# 前置: 安装 CMake
# 下载: https://cmake.org/download/

# CUDA 编译
set CMAKE_ARGS=-DGGML_CUDA=on
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 5.2 macOS

```bash
# 安装 Xcode 命令行工具（提供 clang 编译器）
xcode-select --install

# 安装 CMake（llama-cpp-python 需要）
brew install cmake

# MPS 加速版 llama-cpp-python
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 5.3 Linux (Ubuntu/Debian)

```bash
# 安装编译工具
sudo apt install build-essential cmake

# CUDA 版 llama-cpp-python
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 5.4 Linux (CentOS/RHEL)

```bash
sudo dnf groupinstall "Development Tools"
sudo dnf install cmake
```

---

## 6. Docker 容器化部署

### 6.1 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

# 暴露端口
EXPOSE 8000

# 默认启动 Flutter Desktop
CMD ["llm-studio", "serve", "--host", "127.0.0.1", "--port", "8000"]
```

### 6.2 Docker Compose (含 GPU 支持)

```yaml
version: '3.8'
services:
  llm-studio:
    build: .
    ports:
      - "8000:8000"   # Flutter Desktop
      - "8000:8000"   # API
    volumes:
      - ./models:/app/models
      - ./datasets:/app/datasets
      - ./finetuned_models:/app/finetuned_models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### 6.3 构建和运行

```bash
# 构建镜像
docker build -t llm-studio .

# 运行 Flutter Desktop
docker run -p 8000:8000 -v $(pwd)/models:/app/models llm-studio

# 运行 API 服务
docker run -p 8000:8000 -v $(pwd)/models:/app/models llm-studio llm-studio serve

# GPU 支持（需要 nvidia-docker）
docker run --gpus all -p 8000:8000 -v $(pwd)/models:/app/models llm-studio
```

---

## 7. 项目文件结构

```
LLM-Studio/
├── pyproject.toml               # 构建配置 (PEP 517)
├── requirements.txt             # 依赖列表
├── config.yaml                  # 运行时配置
├── llm_studio/                  # Python 包
│   ├── __init__.py
│   ├── cli.py                   # CLI 入口 (click)
│   ├── config.py                # 配置管理
│   ├── downloader.py            # 模型下载
│   ├── runner.py                # 推理引擎
│   ├── finetuner.py             # LoRA/QLoRA 微调
│   ├── exporter.py              # 模型导出/上传
│   ├── document_loader.py       # 文档解析 (PDF/Word/Excel/...)
│   ├── rag.py                   # RAG 知识库管道
│   ├── vision.py                # 图像识别/OCR
│   ├── api_server.py            # FastAPI REST API
│   └── api_server.py                # Flutter Desktop client
├── models/                      # [运行时] 下载的模型
├── datasets/                    # [运行时] 数据集 & 向量库
├── finetuned_models/            # [运行时] 微调输出
└── sample_data/                 # 示例训练数据
```

---

## 8. 版本与构建信息

| 项目 | 值 |
|------|---|
| 项目名称 | llm-studio |
| 版本号 | 1.0.0 |
| Python 要求 | >=3.9 |
| 构建系统 | setuptools >=68.0 |
| 许可证 | MIT |
| CLI 入口 | `llm_studio.cli:main` |

修改版本号：编辑 `pyproject.toml` 中的 `version` 和 `llm_studio/__init__.py` 中的 `__version__`。

---

## 9. 常见构建问题

| 问题 | 解决方案 |
|------|---------|
| `pip install -e .` 报错 | 确认已在虚拟环境中，且 setuptools 版本 >=68.0 |
| PyInstaller 打包后报 ModuleNotFoundError | 增加 `--hidden-import` 或 `--collect-all` 参数 |
| llama-cpp-python 编译失败 | 安装 CMake + C++ 编译器；或到 GitHub Releases 下载预编译 wheel |
| Docker 构建时 torch 太大 | 使用 `--no-cache-dir`，或在 Dockerfile 中先装 torch 再装其他依赖 |
| PyInstaller 包体积太大 | 使用 `--exclude-module` 排除未使用的库，如排除 `torch.distributed` |
| Windows 下 `pip install` 编译错误 | 安装 Visual Studio Build Tools 的 C++ 桌面开发工作负载 |

---
