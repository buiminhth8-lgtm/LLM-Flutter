"""Gradio Web UI for LLM Studio."""

from pathlib import Path

import gradio as gr

from .adapters import AdapterRepository
from .benchmarks import BenchmarkConfig, BenchmarkRunner
from .config import Config, get_device, get_platform_info
from .downloader import ModelDownloader
from .exporter import ModelExporter
from .finetuner import FineTuneArgs, FineTuner
from .generation import CancellationToken
from .jobs import JobQueue, JobRepository, JobType
from .models import LocalModelRepository
from .models.storage import layout_from_config
from .rag import RAGPipeline
from .runner import BaseRunner, create_runner
from .storage import collect_disk_usage
from .vision import VisionRunner


class LLMStudioUI:
    """Web-based UI for LLM Studio using Gradio."""

    def __init__(self, config: Config):
        self.config = config
        self.downloader = ModelDownloader(config)
        self.exporter = ModelExporter()
        self.model_repository = LocalModelRepository(config)
        layout = layout_from_config(config)
        self.job_repository = JobRepository(layout.jobs_dir / "jobs.sqlite")
        self.job_queue = JobQueue(self.job_repository)
        self.adapter_repository = AdapterRepository(config)
        self.current_runner: BaseRunner | None = None
        self.current_model_path: str | None = None
        self.cancellation_token = CancellationToken()

        # RAG pipeline
        rag_cfg = config.get("rag", {})
        self.rag = RAGPipeline(
            config,
            embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5"),
            chunk_size=rag_cfg.get("chunk_size", 500),
            chunk_overlap=rag_cfg.get("chunk_overlap", 50),
        )
        self.rag.load()

        # Vision runner
        self.vision_runner: VisionRunner | None = None

    def model_management_text(self) -> str:
        models = self.model_repository.list_models(refresh=False)
        if not models:
            return "暂无已索引模型，请点击扫描。"
        lines = []
        for model in models[:100]:
            size_gb = model.size_bytes / (1024**3)
            lines.append(
                f"- {model.display_name} | {model.format.value} | {model.status.value} | "
                f"{size_gb:.2f}GB | {model.quantization or 'none'} | {model.path}"
            )
        return "\n".join(lines)

    def scan_models_job(self) -> str:
        def handler(job, update, cancel):
            update(0.1, "扫描本地模型。")
            models = self.model_repository.scan()
            update(1.0, f"扫描完成: {len(models)} 个模型。")

        job = self.job_queue.submit(JobType.MODEL_SCAN.value, {}, handler)
        return f"已创建扫描任务: {job.id}"

    def adapters_text(self) -> str:
        adapters = self.adapter_repository.list()
        if not adapters:
            return "暂无已发现 LoRA adapter。"
        return "\n".join(
            f"- {item.name} | rank={item.rank} | alpha={item.alpha} | compatible={item.compatible} | {item.path}"
            for item in adapters
        )

    def jobs_text(self) -> str:
        jobs = self.job_repository.list(limit=20)
        if not jobs:
            return "暂无后台任务。"
        return "\n".join(
            f"- {job.id} | {job.type} | {job.status} | {job.progress} | {job.message or ''}"
            for job in jobs
        )

    def storage_text(self) -> str:
        return "\n".join(
            f"- {item.category}: {item.size_bytes / (1024**3):.2f}GB | {item.path}"
            for item in collect_disk_usage(self.config)
        )

    def start_benchmark_job(self, model_id: str) -> str:
        if not model_id:
            return "请选择模型。"

        def handler(job, update, cancel):
            update(0.05, "开始 Benchmark。")
            bench = BenchmarkRunner(self.config, lambda mid: create_runner(mid, self.config))
            bench.run(BenchmarkConfig(model_id=model_id))
            update(1.0, "Benchmark 完成。")

        job = self.job_queue.submit(JobType.BENCHMARK.value, {"model_id": model_id}, handler)
        return f"已创建 Benchmark 任务: {job.id}"

    # ── Download Tab ────────────────────────────────────────────

    def get_registry_choices(self) -> list[str]:
        return [
            f"{m['name']}  ({m['size']}) - {m['description']}"
            for m in self.config.model_registry
        ]

    def get_local_models_text(self) -> str:
        models = self.downloader.list_local_models()
        if not models:
            return "暂无已下载的模型"
        lines = []
        for m in models:
            size_mb = m["size"] / (1024 * 1024)
            size_str = f"{size_mb:.0f}MB" if size_mb < 1024 else f"{size_mb/1024:.1f}GB"
            lines.append(f"? {m['name']}  [{m['type']}]  {size_str}\n  路径: {m['path']}")
        return "\n\n".join(lines)

    def download_registry_model(self, selection: str, progress=None):
        progress = progress or gr.Progress()
        if not selection:
            return "请选择一个模型", self.get_local_models_text()
        model_name = selection.split("  (")[0]
        try:
            progress(0, desc=f"正在下载 {model_name}...")
            path = self.downloader.download_from_registry(model_name)
            return f"? 下载完成: {path}", self.get_local_models_text()
        except Exception as e:
            return f"? 下载失败: {str(e)}", self.get_local_models_text()

    def download_custom_model(self, repo_id: str, model_type: str, filename: str, progress=None):
        progress = progress or gr.Progress()
        if not repo_id:
            return "请输入 HuggingFace Repo ID", self.get_local_models_text()
        try:
            progress(0, desc=f"正在下载 {repo_id}...")
            path = self.downloader.download_model(
                repo_id=repo_id,
                model_type=model_type,
                filename=filename if filename else None,
            )
            return f"? 下载完成: {path}", self.get_local_models_text()
        except Exception as e:
            return f"? 下载失败: {str(e)}", self.get_local_models_text()

    def search_hf_models(self, query: str):
        if not query:
            return "请输入搜索关键词"
        try:
            results = self.downloader.search_models(query)
            lines = []
            for r in results:
                lines.append(
                    f"? **{r['repo_id']}**  ?{r['downloads']}  ?{r['likes']}  "
                    f"[{r['pipeline_tag']}]"
                )
            return "\n".join(lines) if lines else "未找到匹配模型"
        except Exception as e:
            return f"搜索失败: {str(e)}"

    # ── Inference Tab ──────────────────────────────────────────

    def get_local_model_choices(self) -> list[str]:
        models = self.downloader.list_local_models()
        return [m["path"] for m in models]

    def load_model(self, model_path: str, progress=None):
        progress = progress or gr.Progress()
        if not model_path:
            return "请选择或输入模型路径"
        try:
            if self.current_runner:
                self.cancellation_token.cancel()
                self.current_runner.unload()
                self.cancellation_token = CancellationToken()

            progress(0, desc="正在加载模型...")
            self.current_runner = create_runner(model_path, self.config)
            self.current_runner.load()
            self.current_model_path = model_path
            return f"? 模型已加载: {Path(model_path).name}"
        except Exception as e:
            return f"? 加载失败: {str(e)}"

    def unload_model(self):
        if self.current_runner:
            self.cancellation_token.cancel()
            self.current_runner.unload()
            self.current_runner = None
            self.current_model_path = None
            return "模型已卸载"
        return "当前没有加载的模型"

    def chat(self, message: str, history: list, temperature: float, max_tokens: int, top_p: float):
        if not self.current_runner:
            return history + [{"role": "user", "content": message}, {"role": "assistant", "content": "?? 请先加载模型"}]

        history = history + [{"role": "user", "content": message}]
        self.cancellation_token = CancellationToken()

        try:
            response = ""
            for chunk in self.current_runner.generate_stream(
                history,
                cancellation_token=self.cancellation_token,
                temperature=temperature,
                max_tokens=int(max_tokens),
                top_p=top_p,
            ):
                response += chunk

            history = history + [{"role": "assistant", "content": response}]
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"? 生成失败: {str(e)}"}]

        return history

    def stop_generation(self):
        self.cancellation_token.cancel()
        return "已请求停止生成"

    # ── Fine-tune Tab ──────────────────────────────────────────

    def start_finetune(
        self,
        base_model: str,
        dataset_file,
        method: str,
        lora_r: int,
        lora_alpha: int,
        learning_rate: float,
        num_epochs: int,
        batch_size: int,
        max_seq_length: int,
        output_name: str,
        progress=None,
    ):
        progress = progress or gr.Progress()
        if not base_model:
            return "请选择基座模型"
        if dataset_file is None:
            return "请上传训练数据集"

        # Save uploaded dataset
        dataset_path = str(self.config.datasets_dir / Path(dataset_file.name).name)

        import shutil
        shutil.copy2(dataset_file.name, dataset_path)

        output_dir = str(
            self.config.finetune_output_dir / (output_name or "finetune_output")
        )

        args = FineTuneArgs(
            model_path=base_model,
            dataset_path=dataset_path,
            output_dir=output_dir,
            method=method,
            lora_r=int(lora_r),
            lora_alpha=int(lora_alpha),
            learning_rate=learning_rate,
            num_epochs=int(num_epochs),
            batch_size=int(batch_size),
            max_seq_length=int(max_seq_length),
        )

        log_lines = []

        def on_progress(info):
            step = info["step"]
            max_steps = info["max_steps"]
            loss = info.get("loss", 0)
            lr = info.get("learning_rate", 0)
            pct = step / max_steps if max_steps > 0 else 0
            progress(pct, desc=f"Step {step}/{max_steps} | Loss: {loss:.4f}")
            log_lines.append(
                f"Step {step}/{max_steps} | Loss: {loss:.4f} | LR: {lr:.2e}"
            )

        try:
            finetuner = FineTuner(args)
            final_path = finetuner.train(dataset_path, progress_callback=on_progress)
            log_text = "\n".join(log_lines)
            return f"? 微调完成！模型保存至: {final_path}\n\n训练日志:\n{log_text}"
        except Exception as e:
            return f"? 微调失败: {str(e)}"

    # ── Export Tab ─────────────────────────────────────────────

    def get_finetuned_models(self) -> list[str]:
        ft_dir = self.config.finetune_output_dir
        if not ft_dir.exists():
            return []
        models = []
        for item in ft_dir.iterdir():
            if item.is_dir():
                final = item / "final"
                if final.exists():
                    models.append(str(final))
                elif (item / "config.json").exists():
                    models.append(str(item))
        return models

    def upload_model(self, model_path: str, repo_id: str, private: bool, token: str, progress=None):
        progress = progress or gr.Progress()
        if not model_path or not repo_id:
            return "请填写模型路径和目标 Repo ID"
        try:
            progress(0, desc="正在上传...")
            url = self.exporter.upload_to_huggingface(
                model_path=model_path,
                repo_id=repo_id,
                private=private,
                token=token if token else None,
            )
            return f"? 上传成功: {url}"
        except Exception as e:
            return f"? 上传失败: {str(e)}"

    # ── RAG Tab Handlers ───────────────────────────────────

    def rag_ingest_files(self, files, progress=None):
        progress = progress or gr.Progress()
        """Ingest uploaded files into the knowledge base."""
        if not files:
            return "请上传文件", self._rag_status_text()
        total = 0
        errors = []
        for f in files:
            try:
                progress(0, desc=f"正在处理 {Path(f.name).name}...")
                count = self.rag.ingest_file(f.name)
                total += count
            except Exception as e:
                errors.append(f"{Path(f.name).name}: {e}")
        self.rag.save()
        msg = f"? 处理完成，新增 {total} 个文本片段"
        if errors:
            msg += "\n\n?? 以下文件处理失败:\n" + "\n".join(errors)
        return msg, self._rag_status_text()

    def rag_ingest_dir(self, dir_path: str, progress=None):
        progress = progress or gr.Progress()
        if not dir_path:
            return "请输入目录路径", self._rag_status_text()
        try:
            progress(0, desc=f"正在扫描 {dir_path}...")
            count = self.rag.ingest_directory(dir_path)
            self.rag.save()
            return f"? 处理完成，新增 {count} 个文本片段", self._rag_status_text()
        except Exception as e:
            return f"? 处理失败: {e}", self._rag_status_text()

    def rag_clear(self):
        self.rag.clear()
        return "知识库已清空", self._rag_status_text()

    def rag_chat(self, question: str, history: list, top_k: int, temperature: float, max_tokens: int):
        """RAG-enhanced chat: retrieve context then generate."""
        if not self.current_runner:
            return history + [
                {"role": "user", "content": question},
                {"role": "assistant", "content": "?? 请先在「模型推理」页签加载模型"},
            ], ""

        history = history + [{"role": "user", "content": question}]

        # Retrieve
        results = self.rag.query(question, top_k=int(top_k))
        refs = ""
        if results:
            ref_parts = []
            for i, (doc, score) in enumerate(results, 1):
                src = doc.metadata.get("filename", "?")
                ref_parts.append(f"[{i}] {src} (相关度: {score:.2f})\n{doc.content[:200]}...")
            refs = "\n\n".join(ref_parts)

        # Build RAG prompt
        rag_prompt = self.rag.build_rag_prompt(question, top_k=int(top_k))
        rag_messages = history[:-1] + [{"role": "user", "content": rag_prompt}]

        try:
            response = ""
            self.cancellation_token = CancellationToken()
            for chunk in self.current_runner.generate_stream(
                rag_messages,
                cancellation_token=self.cancellation_token,
                temperature=temperature,
                max_tokens=int(max_tokens),
            ):
                response += chunk
            history = history + [{"role": "assistant", "content": response}]
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"? 生成失败: {e}"}]

        return history, refs

    def _rag_status_text(self) -> str:
        count = self.rag.document_count
        sources = self.rag.get_ingested_sources()
        if count == 0:
            return "知识库为空，请上传文档"
        text = f"? 知识库: {count} 个文本片段\n\n来源文件 ({len(sources)} 个):\n"
        for s in sources:
            text += f"  ? {Path(s).name}\n"
        return text

    # ── Vision Tab Handlers ────────────────────────────────

    def load_vision_model(self, model_path: str, progress=None):
        progress = progress or gr.Progress()
        if not model_path:
            return "请输入视觉模型路径"
        try:
            if self.vision_runner:
                self.vision_runner.unload()
            progress(0, desc="正在加载视觉模型...")
            self.vision_runner = VisionRunner(model_path, self.config)
            self.vision_runner.load()
            return f"? 视觉模型已加载: {Path(model_path).name}"
        except Exception as e:
            return f"? 加载失败: {e}"

    def analyze_image(self, image, prompt: str, max_tokens: int, temperature: float):
        if not self.vision_runner:
            return "?? 请先加载视觉模型"
        if image is None:
            return "请上传图片"
        try:
            # Gradio Image component gives a filepath string or numpy array
            if isinstance(image, str):
                img_path = image
            else:
                # Save numpy array as temp image
                import tempfile

                from PIL import Image as PILImage
                pil_img = PILImage.fromarray(image)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                pil_img.save(tmp.name)
                img_path = tmp.name

            response = self.vision_runner.analyze_image(
                img_path, prompt=prompt,
                max_tokens=int(max_tokens), temperature=temperature,
            )
            return response
        except Exception as e:
            return f"? 识别失败: {e}"

    def ocr_image(self, image):
        if not self.vision_runner:
            return "?? 请先加载视觉模型"
        if image is None:
            return "请上传图片"
        try:
            if isinstance(image, str):
                img_path = image
            else:
                import tempfile

                from PIL import Image as PILImage
                pil_img = PILImage.fromarray(image)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                pil_img.save(tmp.name)
                img_path = tmp.name
            return self.vision_runner.ocr_image(img_path)
        except Exception as e:
            return f"? OCR 失败: {e}"

    # ── Build UI ───────────────────────────────────────────────

    def build(self) -> gr.Blocks:
        platform_info = None
        try:
            platform_info = get_platform_info()
        except Exception:
            platform_info = {"os": "Unknown", "error": "Cannot detect platform info"}

        with gr.Blocks(
            title="LLM Studio",
            theme=gr.themes.Soft(),
            css="""
            .main-title { text-align: center; margin-bottom: 0; }
            .sub-title { text-align: center; color: #666; margin-top: 0; }
            """
        ) as app:

            gr.Markdown("# ? LLM Studio", elem_classes="main-title")
            gr.Markdown(
                "大模型下载 · 推理 · 微调 · 知识库 · 图像识别 · API 一站式管理平台",
                elem_classes="sub-title",
            )

            # System info bar
            if platform_info:
                info_parts = [
                    f"? {platform_info.get('os', 'N/A')}",
                    f"? RAM: {platform_info.get('ram_available_gb', '?')}/{platform_info.get('ram_total_gb', '?')} GB",
                ]
                if platform_info.get("cuda_available"):
                    info_parts.append(f"? GPU: {platform_info.get('gpu', 'N/A')} ({platform_info.get('gpu_memory_gb', '?')} GB)")
                elif platform_info.get("mps_available"):
                    info_parts.append("? Apple MPS")
                else:
                    info_parts.append("CPU Only")
                gr.Markdown(f"{'  |  '.join(info_parts)}")

            # ── Tab: Download ──
            with gr.Tab("? 模型下载"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 推荐模型")
                        registry_dropdown = gr.Dropdown(
                            choices=self.get_registry_choices(),
                            label="选择推荐模型",
                            interactive=True,
                        )
                        btn_download_registry = gr.Button("下载选中模型", variant="primary")
                        download_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("---")
                        gr.Markdown("### 自定义下载")
                        custom_repo = gr.Textbox(
                            label="HuggingFace Repo ID",
                            placeholder="例如: Qwen/Qwen2.5-7B-Instruct",
                        )
                        custom_type = gr.Radio(
                            ["transformers", "gguf"], value="transformers", label="模型类型"
                        )
                        custom_filename = gr.Textbox(
                            label="GGUF 文件名 (仅 GGUF 类型)",
                            placeholder="可选, 留空自动检测",
                        )
                        btn_download_custom = gr.Button("下载自定义模型")
                        custom_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("---")
                        gr.Markdown("### 搜索 HuggingFace")
                        search_input = gr.Textbox(label="搜索关键词", placeholder="例如: chinese llm")
                        btn_search = gr.Button("搜索")
                        search_results = gr.Markdown()

                    with gr.Column(scale=1):
                        gr.Markdown("### 已下载模型")
                        local_models_display = gr.Textbox(
                            value=self.get_local_models_text(),
                            label="本地模型列表",
                            interactive=False,
                            lines=20,
                        )
                        btn_refresh = gr.Button("刷新列表")

                btn_download_registry.click(
                    self.download_registry_model,
                    inputs=[registry_dropdown],
                    outputs=[download_status, local_models_display],
                )
                btn_download_custom.click(
                    self.download_custom_model,
                    inputs=[custom_repo, custom_type, custom_filename],
                    outputs=[custom_status, local_models_display],
                )
                btn_search.click(self.search_hf_models, inputs=[search_input], outputs=[search_results])
                btn_refresh.click(lambda: self.get_local_models_text(), outputs=[local_models_display])

            # ── Tab: Inference ──
            with gr.Tab("? 模型推理"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 加载模型")
                        model_path_input = gr.Dropdown(
                            choices=self.get_local_model_choices(),
                            label="选择模型",
                            allow_custom_value=True,
                            interactive=True,
                        )
                        with gr.Row():
                            btn_load = gr.Button("加载模型", variant="primary")
                            btn_unload = gr.Button("卸载模型")
                        load_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("### 参数设置")
                        temperature = gr.Slider(0, 2, value=0.7, step=0.1, label="Temperature")
                        max_tokens = gr.Slider(64, 4096, value=2048, step=64, label="Max Tokens")
                        top_p = gr.Slider(0, 1, value=0.9, step=0.05, label="Top P")

                    with gr.Column(scale=2):
                        chatbot = gr.Chatbot(label="对话", height=500, type="messages")
                        with gr.Row():
                            msg_input = gr.Textbox(
                                label="输入消息",
                                placeholder="在这里输入你的问题...",
                                scale=4,
                            )
                            btn_send = gr.Button("发送", variant="primary", scale=1)
                        with gr.Row():
                            btn_stop = gr.Button("停止生成", variant="stop")
                            btn_clear = gr.Button("清空对话")

                btn_load.click(self.load_model, inputs=[model_path_input], outputs=[load_status])
                btn_unload.click(self.unload_model, outputs=[load_status])
                btn_send.click(
                    self.chat,
                    inputs=[msg_input, chatbot, temperature, max_tokens, top_p],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[msg_input])
                msg_input.submit(
                    self.chat,
                    inputs=[msg_input, chatbot, temperature, max_tokens, top_p],
                    outputs=[chatbot],
                ).then(lambda: "", outputs=[msg_input])
                btn_stop.click(self.stop_generation, outputs=[load_status])
                btn_clear.click(lambda: (self.cancellation_token.cancel(), [])[1], outputs=[chatbot])

            # ── Tab: Fine-tune ──
            with gr.Tab("? 模型微调"):
                gr.Markdown(
                    "### LoRA / QLoRA 微调\n"
                    "上传 JSONL 或 JSON 格式的训练数据集，支持 Alpaca 和 ShareGPT 格式。"
                )
                with gr.Row():
                    with gr.Column():
                        ft_base_model = gr.Dropdown(
                            choices=self.get_local_model_choices(),
                            label="选择基座模型",
                            allow_custom_value=True,
                            interactive=True,
                        )
                        ft_dataset = gr.File(label="上传训练数据集 (.jsonl / .json)")
                        ft_method = gr.Radio(["lora", "qlora"], value="lora", label="微调方法")
                        ft_output_name = gr.Textbox(
                            label="输出名称", value="my_finetuned_model",
                            placeholder="微调模型保存名称",
                        )

                    with gr.Column():
                        gr.Markdown("### 超参数配置")
                        ft_lora_r = gr.Slider(4, 128, value=16, step=4, label="LoRA Rank (r)")
                        ft_lora_alpha = gr.Slider(8, 256, value=32, step=8, label="LoRA Alpha")
                        ft_lr = gr.Number(value=2e-4, label="学习率 (Learning Rate)")
                        ft_epochs = gr.Slider(1, 20, value=3, step=1, label="训练轮数 (Epochs)")
                        ft_batch = gr.Slider(1, 32, value=4, step=1, label="Batch Size")
                        ft_seq_len = gr.Slider(128, 2048, value=512, step=128, label="最大序列长度")

                btn_finetune = gr.Button("? 开始微调", variant="primary", size="lg")
                ft_output = gr.Textbox(label="训练输出", interactive=False, lines=15)

                btn_finetune.click(
                    self.start_finetune,
                    inputs=[
                        ft_base_model, ft_dataset, ft_method,
                        ft_lora_r, ft_lora_alpha, ft_lr,
                        ft_epochs, ft_batch, ft_seq_len, ft_output_name,
                    ],
                    outputs=[ft_output],
                )

                # Dataset format help
                with gr.Accordion("? 数据集格式说明", open=False):
                    gr.Markdown("""
**Alpaca 格式 (JSONL):**
```json
{"instruction": "翻译下面的句子", "input": "Hello world", "output": "你好世界"}
{"instruction": "写一首诗", "input": "", "output": "春风拂面来，花开满园栽。"}
```

**ShareGPT 格式 (JSONL):**
```json
{"conversations": [{"from": "human", "value": "你好"}, {"from": "gpt", "value": "你好！有什么可以帮助你的吗？"}]}
```
                    """)

            # ── Tab: Export ──
            with gr.Tab("? 模型导出/上传"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 微调模型列表")
                        ft_model_dropdown = gr.Dropdown(
                            choices=self.get_finetuned_models(),
                            label="选择微调模型",
                            allow_custom_value=True,
                            interactive=True,
                        )
                        btn_refresh_ft = gr.Button("刷新列表")

                        gr.Markdown("### 上传到 HuggingFace")
                        upload_repo_id = gr.Textbox(
                            label="目标 Repo ID",
                            placeholder="例如: your-username/my-model",
                        )
                        upload_private = gr.Checkbox(value=True, label="设为私有仓库")
                        upload_token = gr.Textbox(
                            label="HuggingFace Token (可选)",
                            placeholder="留空则使用已登录的账号",
                            type="password",
                        )
                        btn_upload = gr.Button("上传模型", variant="primary")
                        upload_status = gr.Textbox(label="上传状态", interactive=False)

                    with gr.Column():
                        gr.Markdown("### 模型保存")
                        save_source = gr.Textbox(label="源模型路径")
                        save_dest = gr.Textbox(label="目标保存路径")
                        btn_save_copy = gr.Button("另存为副本")
                        save_status = gr.Textbox(label="状态", interactive=False)

                btn_refresh_ft.click(
                    lambda: gr.update(choices=self.get_finetuned_models()),
                    outputs=[ft_model_dropdown],
                )
                btn_upload.click(
                    self.upload_model,
                    inputs=[ft_model_dropdown, upload_repo_id, upload_private, upload_token],
                    outputs=[upload_status],
                )
                btn_save_copy.click(
                    lambda src, dst: (
                        f"? 已保存到: {self.exporter.save_model_copy(src, dst)}"
                        if src and dst
                        else "请填写源路径和目标路径"
                    ),
                    inputs=[save_source, save_dest],
                    outputs=[save_status],
                )

            # ── Tab: RAG Knowledge Base ──
            with gr.Tab("? 知识库 (RAG)"):
                gr.Markdown(
                    "### 文档投喂与知识库问答\n"
                    "上传本地文档（Word、PDF、Excel、TXT、Markdown、HTML、PPT 等），"
                    "构建知识库，基于文档内容增强大模型回答。"
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 投喂文档")
                        rag_files = gr.File(
                            label="上传文档（支持多文件）",
                            file_count="multiple",
                            file_types=[".pdf", ".docx", ".doc", ".txt", ".md", ".csv",
                                        ".xlsx", ".xls", ".html", ".htm", ".pptx", ".json", ".jsonl"],
                        )
                        btn_rag_ingest = gr.Button("投喂到知识库", variant="primary")
                        rag_ingest_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("---")
                        gr.Markdown("### 批量投喂目录")
                        rag_dir_input = gr.Textbox(
                            label="本地目录路径",
                            placeholder="例如: C:\\Documents\\MyData",
                        )
                        btn_rag_dir = gr.Button("投喂整个目录")
                        rag_dir_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("---")
                        btn_rag_clear = gr.Button("?? 清空知识库", variant="stop")
                        rag_clear_status = gr.Textbox(label="状态", interactive=False)

                    with gr.Column(scale=1):
                        gr.Markdown("### 知识库状态")
                        rag_status_display = gr.Textbox(
                            value=self._rag_status_text(),
                            label="当前知识库",
                            interactive=False,
                            lines=10,
                        )
                        btn_rag_refresh = gr.Button("刷新状态")

                        gr.Markdown("### 支持的文件格式")
                        gr.Markdown(
                            "PDF · Word (.docx) · Excel (.xlsx/.xls) · CSV · "
                            "TXT · Markdown · HTML · PowerPoint (.pptx) · JSON/JSONL"
                        )

                gr.Markdown("---")
                gr.Markdown("### 知识库问答（需先在「模型推理」页加载模型）")
                with gr.Row():
                    with gr.Column(scale=2):
                        rag_chatbot = gr.Chatbot(label="知识库对话", height=400, type="messages")
                        with gr.Row():
                            rag_msg = gr.Textbox(label="输入问题", placeholder="基于知识库内容提问...", scale=4)
                            btn_rag_send = gr.Button("发送", variant="primary", scale=1)
                        btn_rag_clear_chat = gr.Button("清空对话")
                    with gr.Column(scale=1):
                        rag_top_k = gr.Slider(1, 20, value=5, step=1, label="检索片段数 (Top K)")
                        rag_temp = gr.Slider(0, 2, value=0.7, step=0.1, label="Temperature")
                        rag_max_tokens = gr.Slider(64, 4096, value=2048, step=64, label="Max Tokens")
                        rag_refs = gr.Textbox(label="参考文档片段", interactive=False, lines=12)

                btn_rag_ingest.click(
                    self.rag_ingest_files, inputs=[rag_files],
                    outputs=[rag_ingest_status, rag_status_display],
                )
                btn_rag_dir.click(
                    self.rag_ingest_dir, inputs=[rag_dir_input],
                    outputs=[rag_dir_status, rag_status_display],
                )
                btn_rag_clear.click(
                    self.rag_clear, outputs=[rag_clear_status, rag_status_display],
                )
                btn_rag_refresh.click(
                    lambda: self._rag_status_text(), outputs=[rag_status_display],
                )
                btn_rag_send.click(
                    self.rag_chat,
                    inputs=[rag_msg, rag_chatbot, rag_top_k, rag_temp, rag_max_tokens],
                    outputs=[rag_chatbot, rag_refs],
                ).then(lambda: "", outputs=[rag_msg])
                rag_msg.submit(
                    self.rag_chat,
                    inputs=[rag_msg, rag_chatbot, rag_top_k, rag_temp, rag_max_tokens],
                    outputs=[rag_chatbot, rag_refs],
                ).then(lambda: "", outputs=[rag_msg])
                btn_rag_clear_chat.click(lambda: ([], ""), outputs=[rag_chatbot, rag_refs])

            # ── Tab: Vision ──
            with gr.Tab("?? 图像识别"):
                gr.Markdown(
                    "### 图像理解与 OCR\n"
                    "加载视觉语言模型（如 Qwen2-VL），对图片进行内容描述、问答、文字提取。"
                )
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 加载视觉模型")
                        vision_model_input = gr.Dropdown(
                            choices=self.get_local_model_choices(),
                            label="选择视觉模型路径",
                            allow_custom_value=True,
                            interactive=True,
                        )
                        btn_load_vision = gr.Button("加载视觉模型", variant="primary")
                        vision_load_status = gr.Textbox(label="状态", interactive=False)

                        gr.Markdown("### 推荐视觉模型")
                        vision_registry = self.config.get("vision_model_registry", [])
                        if vision_registry:
                            for vm in vision_registry:
                                gr.Markdown(f"? **{vm['name']}** ({vm.get('size','')}) - {vm.get('description','')}")

                    with gr.Column(scale=2):
                        gr.Markdown("### 图片分析")
                        vision_image = gr.Image(label="上传图片", type="filepath")
                        vision_prompt = gr.Textbox(
                            label="提问 / 指令",
                            value="请详细描述这张图片的内容。",
                            placeholder="你可以问关于图片的任何问题...",
                        )
                        with gr.Row():
                            vision_max_tokens = gr.Slider(64, 2048, value=1024, step=64, label="Max Tokens")
                            vision_temp = gr.Slider(0, 2, value=0.7, step=0.1, label="Temperature")
                        with gr.Row():
                            btn_analyze = gr.Button("? 分析图片", variant="primary")
                            btn_ocr = gr.Button("? OCR文字识别")
                        vision_output = gr.Textbox(label="识别结果", interactive=False, lines=12)

                btn_load_vision.click(
                    self.load_vision_model, inputs=[vision_model_input],
                    outputs=[vision_load_status],
                )
                btn_analyze.click(
                    self.analyze_image,
                    inputs=[vision_image, vision_prompt, vision_max_tokens, vision_temp],
                    outputs=[vision_output],
                )
                btn_ocr.click(
                    self.ocr_image, inputs=[vision_image], outputs=[vision_output],
                )

            with gr.Tab("模型管理"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 本地模型")
                        model_management_output = gr.Textbox(
                            value=self.model_management_text(),
                            label="模型索引",
                            interactive=False,
                            lines=12,
                        )
                        btn_model_refresh = gr.Button("刷新列表")
                        btn_model_scan = gr.Button("后台扫描模型")
                        model_scan_status = gr.Textbox(label="扫描任务", interactive=False)

                    with gr.Column():
                        gr.Markdown("### 下载与任务")
                        jobs_output = gr.Textbox(
                            value=self.jobs_text(),
                            label="最近任务",
                            interactive=False,
                            lines=12,
                        )
                        btn_jobs_refresh = gr.Button("刷新任务")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### LoRA 适配器")
                        adapters_output = gr.Textbox(
                            value=self.adapters_text(),
                            label="适配器",
                            interactive=False,
                            lines=10,
                        )
                        btn_adapters_refresh = gr.Button("刷新适配器")

                    with gr.Column():
                        gr.Markdown("### Benchmark")
                        benchmark_model = gr.Dropdown(
                            choices=self.get_local_model_choices(),
                            label="选择模型",
                            allow_custom_value=True,
                            interactive=True,
                        )
                        btn_benchmark = gr.Button("启动 Benchmark")
                        benchmark_status = gr.Textbox(label="Benchmark 任务", interactive=False)

                gr.Markdown("### 存储占用")
                storage_output = gr.Textbox(
                    value=self.storage_text(),
                    label="磁盘空间",
                    interactive=False,
                    lines=8,
                )
                btn_storage_refresh = gr.Button("刷新存储")

                btn_model_refresh.click(self.model_management_text, outputs=[model_management_output])
                btn_model_scan.click(self.scan_models_job, outputs=[model_scan_status])
                btn_jobs_refresh.click(self.jobs_text, outputs=[jobs_output])
                btn_adapters_refresh.click(self.adapters_text, outputs=[adapters_output])
                btn_benchmark.click(self.start_benchmark_job, inputs=[benchmark_model], outputs=[benchmark_status])
                btn_storage_refresh.click(self.storage_text, outputs=[storage_output])

            # ── Tab: API ──
            with gr.Tab("? API 服务"):
                gr.Markdown(
                    "### REST API 服务\n"
                    "启动 API 服务后，第三方程序可通过 HTTP 接口调用已加载的模型。\n"
                    "API 兼容 OpenAI Chat Completions 格式。"
                )
                api_cfg = self.config.get("api", {})
                api_port = api_cfg.get("port", 8000)

                gr.Markdown(f"""
**启动方式（命令行）:**
```bash
llm-studio serve --port {api_port}
```

---

### ? API 端点一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/v1/models` | 列出已加载模型 |
| POST | `/v1/models/load` | 加载模型 |
| POST | `/v1/models/unload` | 卸载模型 |
| POST | `/v1/chat/completions` | 对话补全 (OpenAI 兼容) |
| POST | `/v1/rag/ingest` | 投喂文档到知识库 |
| POST | `/v1/rag/ingest/upload` | 上传文件到知识库 |
| POST | `/v1/rag/query` | RAG 知识库问答 |
| GET  | `/v1/rag/status` | 查看知识库状态 |
| POST | `/v1/rag/clear` | 清空知识库 |
| POST | `/v1/vision/analyze` | 图片分析 |
| POST | `/v1/vision/analyze/upload` | 上传图片分析 |
| POST | `/v1/vision/ocr` | 图片 OCR |

---

### ? 调用示例

**Python:**
```python
import requests

# 加载模型
requests.post("http://localhost:{api_port}/v1/models/load", json={{
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct",
    "model_type": "text"
}})

# 对话
resp = requests.post("http://localhost:{api_port}/v1/chat/completions", json={{
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct",
    "messages": [{{"role": "user", "content": "你好"}}],
    "temperature": 0.7,
    "max_tokens": 1024
}})
print(resp.json()["choices"][0]["message"]["content"])
```

**cURL:**
```bash
curl -X POST http://localhost:{api_port}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"./models/Qwen--Qwen2.5-1.5B-Instruct","messages":[{{"role":"user","content":"你好"}}]}}'
```

**投喂文档:**
```python
# 投喂本地文件
requests.post("http://localhost:{api_port}/v1/rag/ingest", json={{
    "file_path": "C:/Documents/manual.pdf"
}})

# RAG 问答
resp = requests.post("http://localhost:{api_port}/v1/rag/query", json={{
    "question": "产品有哪些功能？",
    "model": "./models/Qwen--Qwen2.5-1.5B-Instruct",
    "top_k": 5
}})
print(resp.json()["answer"])
```
                """)

            # ── Tab: System Info ──
            with gr.Tab("?? 系统信息"):
                if platform_info:
                    info_md = "### 系统环境\n\n"
                    for k, v in platform_info.items():
                        label = {
                            "os": "操作系统",
                            "os_version": "系统版本",
                            "arch": "架构",
                            "python": "Python 版本",
                            "cpu_count": "CPU 核心数",
                            "ram_total_gb": "总内存 (GB)",
                            "ram_available_gb": "可用内存 (GB)",
                            "cuda_available": "CUDA 可用",
                            "mps_available": "Apple MPS 可用",
                            "gpu": "GPU",
                            "gpu_memory_gb": "GPU 显存 (GB)",
                        }.get(k, k)
                        info_md += f"- **{label}**: {v}\n"
                    info_md += f"\n- **推理设备**: {get_device()}\n"
                    gr.Markdown(info_md)
                else:
                    gr.Markdown("无法获取系统信息")

        return app


def launch_ui(config: Config, share: bool = False, port: int = 7860):
    """Launch the Gradio web UI."""
    ui = LLMStudioUI(config)
    app = ui.build()
    app.launch(server_name="0.0.0.0", server_port=port, share=share)
