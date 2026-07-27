# ? LLM Studio

**跨平台大语言模型一站式管理平台** — 下载、推理、微调、知识库问答、图像识别、API 服务，一个工具全搞定。

[![Python 3.10-3.12](https://img.shields.io/badge/Python-3.10--3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

<p align="center">
  <strong>NVIDIA CUDA GPU</strong> · <strong>Apple MPS (M1/M2/M3/M4)</strong> · <strong>CPU</strong> &nbsp;自动检测，零配置运行
</p>

---

## ? 核心特性

| 功能 | 说明 |
|------|------|
| ? **模型下载** | HuggingFace 一键下载，内置 7+ 精选模型，支持 Transformers / GGUF 双格式 |
| ? **模型推理** | 双引擎推理（Transformers + llama-cpp-python），流式输出，自动 4-bit 量化 |
| ? **LoRA/QLoRA 微调** | 参数高效微调，Alpaca / ShareGPT 数据集，实时训练进度，断点续训 |
| ? **RAG 知识库** | 投喂 PDF/Word/Excel/PPT 等 10+ 格式文档，检索增强问答，来源追溯 |
| ?? **图像识别** | 视觉语言模型，图片描述/问答/OCR，支持 PaddleOCR / EasyOCR |
| ? **REST API** | OpenAI 兼容接口（`/v1/chat/completions`），SSE 流式，可对接任意第三方客户端 |
| ? **API 密钥管理** | 内置 Web 管理后台，可视化创建/管理用户和 API Key |
| ? **Web 界面** | Gradio 8 页签可视化操作，浏览器即用 |
| ?? **CLI 命令行** | Click + Rich 终端工具，完整命令行操作能力 |
| ? **模型导出** | LoRA 合并、HuggingFace 上传、GGUF 转换 |

---

## ? 快速开始

### 安装

```bash
git clone https://github.com/airen3339/LLM-Studio.git
cd LLM-Studio

# 创建虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

> **GPU 加速**：CUDA PyTorch 不在普通 `requirements.txt` 中安装。Windows NVIDIA 用户请先运行 `.\scripts\install_windows_cuda.ps1`，确认 `torch.__version__` 不是 `+cpu` 且 `torch.cuda.is_available()` 为 `True`。

### Windows 11 + RTX 5060 Laptop 8GB 推荐安装

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

.\scripts\install_windows_cuda.ps1
.\scripts\install_base.ps1
python -m llm_studio.runtime.diagnostics
```

推荐生产环境是 **Python 3.12 x64**。项目支持范围为 Python `>=3.10,<3.13`；暂不推荐 Python 3.14，因为 `llama-cpp-python`、量化和 OCR/CUDA 扩展更容易回退到源码编译或遇到 ABI 兼容问题。

### 三种使用方式

```bash
# 1. Web 界面
llm-studio ui

# 2. 命令行
llm-studio model download "Qwen2.5-7B-Instruct"
llm-studio chat ./models/Qwen--Qwen2.5-7B-Instruct

# 3. API 服务
llm-studio serve
```

---

## ? 模型下载

```bash
# 查看推荐模型列表
llm-studio model registry

# 一键下载
llm-studio model download "Qwen2.5-7B-Instruct"

# 下载 GGUF 量化版（更小更快）
llm-studio model download "Qwen2.5-1.5B-Instruct-GGUF"

# 从 HuggingFace 下载任意模型
llm-studio model download Qwen/Qwen2.5-7B-Instruct

# 搜索模型
llm-studio model search "chinese llm"
```

**内置推荐模型**：

| 模型 | 大小 | 格式 | 说明 |
|------|------|------|------|
| Qwen2.5-1.5B-Instruct | 3 GB | Transformers | 通义千问轻量模型 |
| Qwen2.5-7B-Instruct | 15 GB | Transformers | 通义千问中英文模型 |
| Llama-3.1-8B-Instruct | 16 GB | Transformers | Meta Llama 3.1 |
| Mistral-7B-Instruct | 15 GB | Transformers | Mistral AI 高效模型 |
| Phi-3-mini-4k-instruct | 7.6 GB | Transformers | 微软小型高效模型 |
| Qwen2.5-1.5B-Instruct-GGUF | 1 GB | GGUF | Q4_K_M 量化版 |
| Llama-3.1-8B-Instruct-GGUF | 4.9 GB | GGUF | Q4_K_M 量化版 |

---

## ? 推理对话

```bash
# 交互式对话
llm-studio chat ./models/Qwen--Qwen2.5-7B-Instruct
```

- **双推理引擎**：自动根据模型格式选择 Transformers 或 llama-cpp-python
- **流式输出**：逐 token 实时显示
- **CUDA 4-bit 量化**：仅在配置选择、CUDA 可用、bitsandbytes 已安装且 4-bit 探针成功时启用
- **可调参数**：Temperature / Top-P / Top-K / Max Tokens / Repeat Penalty

---

## ? LoRA / QLoRA 微调

```bash
# LoRA 微调
llm-studio finetune ./models/Qwen--Qwen2.5-1.5B-Instruct ./datasets/my_data.jsonl

# QLoRA（更省显存）
llm-studio finetune ./models/Qwen--Qwen2.5-7B-Instruct ./datasets/data.jsonl --method qlora

# 自定义训练参数
llm-studio finetune ./models/xxx ./data.jsonl --epochs 5 --lr 1e-4 --lora-r 32
```

**支持的数据集格式**：

```jsonl
# Alpaca 格式
{"instruction": "翻译为英文", "input": "今天天气真好", "output": "The weather is really nice today."}

# ShareGPT 格式
{"conversations": [{"from": "human", "value": "你好"}, {"from": "gpt", "value": "你好！有什么可以帮助你？"}]}
```

---

## ? RAG 知识库

让大模型基于你的本地文档进行回答，支持 **10+ 文档格式**：

> PDF · Word · Excel · CSV · PowerPoint · HTML · EPUB · TXT · Markdown · JSON

```bash
# 投喂文档
llm-studio rag ingest ./docs/技术手册.pdf
llm-studio rag ingest ./knowledge_base/     # 整个目录

# 知识库问答
llm-studio rag query "系统支持的最大并发数是多少？"

# 查看知识库状态
llm-studio rag status
```

**工作原理**：文档分块 → sentence-transformers 向量化 → 相似度检索 → 注入 Prompt → 大模型生成回答

---

## ?? 图像识别

```python
# API 调用示例
requests.post("http://localhost:8000/v1/vision/analyze", json={
    "model": "./models/Qwen2-VL-2B-Instruct",
    "image_path": "photo.jpg",
    "prompt": "描述这张图片"
}, headers=HEADERS)
```

- **图片描述**：AI 自动分析图片内容
- **图片问答**：针对图片提出特定问题
- **OCR 文字识别**：中英文文字提取（PaddleOCR → EasyOCR → 视觉模型兜底）

---

## ? REST API

启动 OpenAI 兼容的 API 服务：

```bash
llm-studio serve                 # http://localhost:8000
llm-studio serve --port 9000     # 自定义端口
```

### OpenAI 兼容调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="YOUR_KEY",
    default_headers={"X-User-ID": "admin"},
)

response = client.chat.completions.create(
    model="auto",                    # 自动选择模型
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
)
for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

### 主要端点

| 端点 | 说明 |
|------|------|
| `GET /v1/models` | 列出所有可用模型 |
| `POST /v1/chat/completions` | 聊天补全（支持 SSE 流式） |
| `POST /v1/rag/ingest` | 投喂文档到知识库 |
| `POST /v1/rag/query` | RAG 检索增强问答 |
| `POST /v1/vision/analyze` | 图片识别分析 |
| `GET /health` | 健康检查 |

完整 API 文档（Swagger UI）：`http://localhost:8000/docs`

---

## ? API 密钥管理后台

启动 API 服务后访问 **`http://localhost:8000/admin`** 进入管理后台：

- 不再提供硬编码默认密码；首次启动会读取环境变量 `LLM_STUDIO_INITIAL_ADMIN_PASSWORD`，未设置时生成一次性随机初始密码并只在启动日志显示
- 首次启动自动创建管理员用户和随机 API Key，API Key 只在创建或重置时显示一次
- 可视化创建用户、查看/重置密钥、启用/禁用用户
- 用户数据持久化存储，重启不丢失

**认证方式**：请求头携带 `X-User-ID` + `X-API-Key`

```bash
curl -H "X-User-ID: admin" -H "X-API-Key: sk-llmstudio-xxx" \
  http://localhost:8000/v1/models
```

---

## ? Web 界面

```bash
llm-studio ui
```

浏览器打开 `http://localhost:7860`，8 个功能页签：

? 模型下载 · ? 模型推理 · ? 模型微调 · ? 知识库(RAG) · ?? 图像识别 · ? 模型导出 · ? API 服务 · ?? 系统信息

---

## ? 项目结构

```
LLM-Studio/
├── config.yaml                  # 全局配置
├── requirements.txt             # Python 依赖
├── pyproject.toml               # 项目打包配置
├── llm_studio/
│   ├── cli.py                   # CLI 命令行入口
│   ├── config.py                # 配置管理
│   ├── downloader.py            # 模型下载
│   ├── runner.py                # 推理引擎 (Transformers + GGUF)
│   ├── finetuner.py             # LoRA/QLoRA 微调
│   ├── document_loader.py       # 多格式文档解析
│   ├── rag.py                   # RAG 向量检索管道
│   ├── vision.py                # 视觉模型 + OCR
│   ├── api_server.py            # FastAPI REST API 服务
│   ├── admin.py                 # API 用户/密钥管理
│   ├── admin_ui.html            # 管理后台前端
│   ├── exporter.py              # 模型导出/上传
│   └── web_ui.py                # Gradio Web 界面
├── docs/
│   ├── 功能说明.md
│   ├── 环境安装说明.md
│   ├── 编译说明.md
│   └── API接口说明.md
├── models/                      # 模型存放目录
├── datasets/                    # 数据集目录
└── finetuned_models/            # 微调输出目录
```

---

## ?? 配置

编辑 `config.yaml` 自定义：

```yaml
models_dir: "./models"                    # 模型存储路径
inference:
  temperature: 0.7                        # 推理参数
  max_tokens: 2048
rag:
  embedding_model: "BAAI/bge-small-zh-v1.5"  # RAG 嵌入模型
  chunk_size: 500
auth:
  enabled: true                           # API 认证开关
api:
  port: 8000
```

---

## ? 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| Python | 3.10+ | 3.12 x64 |
| 内存 | 8 GB | 16+ GB |
| 磁盘 | 10 GB | 50+ GB |
| GPU | 可选（CPU 可运行） | NVIDIA 8GB+ VRAM |

**支持的操作系统**：Windows 10+ · macOS 12.3+ (MPS) · Ubuntu 20.04+

---

## 依赖分层

根目录 `requirements.txt` 只安装基础推理与 Web UI：

```text
-r requirements/base.txt
-r requirements/web.txt
```

可选能力按需安装：

| 文件 | 用途 |
|------|------|
| `requirements/rag.txt` | RAG、文档解析和 embedding |
| `requirements/finetune.txt` | LoRA/QLoRA 微调 |
| `requirements/vision.txt` | 基础图像处理 |
| `requirements/ocr-easyocr.txt` | EasyOCR |
| `requirements/ocr-paddle.txt` | PaddleOCR |
| `requirements/cuda.txt` | bitsandbytes 与 GPTQModel |
| `requirements/gguf.txt` | llama-cpp-python / GGUF |
| `requirements/dev.txt` | pytest、ruff、mypy |

`torch`、`torchvision`、`torchaudio` 必须通过 `scripts/install_windows_cuda.ps1` 单独安装。不要使用 `torch>=2.1.0` 作为普通依赖，因为 CPU wheel 也能满足该条件。

AutoGPTQ 已从默认依赖移除；GPTQModel 是可选 CUDA 后端：

```powershell
.\scripts\install_optional_cuda.ps1
```

GGUF 后端安装：

```powershell
.\scripts\install_optional_gguf.ps1
```

安装后运行诊断：

```powershell
.\scripts\diagnose_environment.ps1
python -m llm_studio.runtime.diagnostics
```

## RTX 5060 8GB 加载建议

| 模型规模 | 默认建议 |
|----------|----------|
| 1B-3B | CUDA + BF16/FP16，不强制 4-bit |
| 7B/8B | 优先 4-bit 或 GGUF Q4_K_M，启用 CPU offload，GPU max_memory 建议 7GiB |
| 14B+ | 默认拒绝全 GPU 加载；需要 GGUF、4-bit/offload 或更大显存 |

默认 `trust_remote_code: false`。只有在你信任模型仓库代码时才显式打开。

## 第二阶段运行时改进

- API、CLI 和 Web UI 统一使用 `ChatMessage` 与 `PromptBuilder`，多轮 user/assistant 历史和 system prompt 不再丢失。
- 无 chat template 的模型使用 `<|system|>`、`<|user|>`、`<|assistant|>` 回退模板。
- 流式生成支持后台线程异常回传、超时和取消。
- Web UI 提供停止生成按钮；API 客户端断开会取消生成。
- 单 GPU 推理默认并发为 1，队列上限默认为 8。
- RAG 默认 embedding 设备为 CPU，索引保存 embedding 模型、维度和 schema 版本。
- 微调默认使用动态 padding 和 assistant-only loss。
- 管理员密码使用 Argon2id，API Key 只保存哈希。

诊断：

```powershell
python -m llm_studio.runtime.diagnostics
python -m llm_studio.cli doctor
```

更多文档：

- [RTX5060_RUNTIME_GUIDE.md](docs/RTX5060_RUNTIME_GUIDE.md)
- [RAG_GUIDE.md](docs/RAG_GUIDE.md)
- [FINETUNE_LOW_VRAM_GUIDE.md](docs/FINETUNE_LOW_VRAM_GUIDE.md)
- [API_SECURITY_GUIDE.md](docs/API_SECURITY_GUIDE.md)

## 常见错误

| 现象 | 处理 |
|------|------|
| `torch` 显示 `+cpu` | 运行 `.\scripts\install_windows_cuda.ps1`，不要从普通 PyPI 装 torch |
| `torch.cuda.is_available=False` | 检查 NVIDIA 驱动、CUDA wheel 索引和虚拟环境 |
| `auto-gptq` 构建找不到 torch | AutoGPTQ 已移除，改用可选 `gptqmodel` |
| `llama-cpp-python` 走源码编译 | 使用 Python 3.12；Python 3.14 可能缺少 wheel |
| llama.cpp 实际为 CPU 版 | 运行 diagnostics 查看 `llama.cpp CUDA`，必要时重装 CUDA 构建 |
| `bitsandbytes no kernel image` | 4-bit 探针失败时使用 BF16/FP16 或 GGUF，不要强制 bnb4 |
| CUDA OOM | 降低 `max_new_tokens/n_ctx`，使用 GGUF/4-bit，确认 `max_gpu_memory: 7GiB` |
| `trust_remote_code` 风险 | 默认关闭；只对可信模型开启 |

---

## ? 文档

| 文档 | 说明 |
|------|------|
| [功能说明](docs/功能说明.md) | 完整功能模块详解 |
| [环境安装说明](docs/环境安装说明.md) | 各平台安装指南、GPU 配置 |
| [编译说明](docs/编译说明.md) | 打包发布、Docker 部署 |
| [API 接口说明](docs/API接口说明.md) | REST API 完整文档、认证方式、调用示例 |

---

## License

MIT
