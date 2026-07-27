"""CLI entry point for LLM Studio."""

import sys
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config, get_platform_info, get_device

console = Console()


def get_config(config_path=None) -> Config:
    return Config(config_path)


@click.group()
@click.option("--config", "-c", default=None, help="Path to config.yaml")
@click.pass_context
def cli(ctx, config):
    """? LLM Studio - 大模型下载·推理·微调 一站式工具"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config(config)


# ── System Info ──────────────────────────────────────────

@cli.command()
def info():
    """显示系统信息"""
    with console.status("正在检测系统信息..."):
        info = get_platform_info()

    table = Table(title="?? 系统信息")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="green")

    labels = {
        "os": "操作系统", "os_version": "系统版本", "arch": "架构",
        "python": "Python", "cpu_count": "CPU 核心数",
        "ram_total_gb": "总内存 (GB)", "ram_available_gb": "可用内存 (GB)",
        "cuda_available": "CUDA", "mps_available": "Apple MPS",
        "gpu": "GPU", "gpu_memory_gb": "GPU 显存 (GB)",
    }
    for k, v in info.items():
        table.add_row(labels.get(k, k), str(v))
    table.add_row("推理设备", get_device())
    console.print(table)


# ── Model Download ───────────────────────────────────────

@cli.group()
def model():
    """模型管理（下载、列表、删除）"""
    pass


@model.command("list")
@click.pass_context
def model_list(ctx):
    """列出已下载的模型"""
    from .downloader import ModelDownloader
    dl = ModelDownloader(ctx.obj["config"])
    models = dl.list_local_models()

    if not models:
        console.print("[yellow]暂无已下载的模型[/yellow]")
        return

    table = Table(title="? 本地模型")
    table.add_column("名称", style="cyan")
    table.add_column("类型", style="magenta")
    table.add_column("大小", style="green")
    table.add_column("路径")

    for m in models:
        size_mb = m["size"] / (1024 * 1024)
        size_str = f"{size_mb:.0f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
        table.add_row(m["name"], m["type"], size_str, m["path"])

    console.print(table)


@model.command("registry")
@click.pass_context
def model_registry(ctx):
    """显示推荐模型列表"""
    registry = ctx.obj["config"].model_registry

    table = Table(title="? 推荐模型")
    table.add_column("名称", style="cyan")
    table.add_column("类型", style="magenta")
    table.add_column("大小", style="green")
    table.add_column("说明")

    for m in registry:
        table.add_row(m["name"], m.get("type", "transformers"), m.get("size", ""), m.get("description", ""))

    console.print(table)


@model.command("download")
@click.argument("name_or_repo")
@click.option("--type", "-t", "model_type", default="transformers", help="模型类型: transformers / gguf")
@click.option("--filename", "-f", default=None, help="GGUF 文件名")
@click.pass_context
def model_download(ctx, name_or_repo, model_type, filename):
    """下载模型 (可用推荐名称或 HuggingFace Repo ID)"""
    from .downloader import ModelDownloader
    dl = ModelDownloader(ctx.obj["config"])

    # Check if it's a registry name
    registry_names = [m["name"] for m in ctx.obj["config"].model_registry]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"正在下载 {name_or_repo}...", total=None)

        try:
            if name_or_repo in registry_names:
                path = dl.download_from_registry(name_or_repo)
            else:
                path = dl.download_model(name_or_repo, model_type, filename)
            progress.update(task, completed=True)
            console.print(f"\n[green]? 下载完成: {path}[/green]")
        except Exception as e:
            console.print(f"\n[red]? 下载失败: {e}[/red]")


@model.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=10, help="最多返回结果数")
@click.pass_context
def model_search(ctx, query, limit):
    """搜索 HuggingFace 模型"""
    from .downloader import ModelDownloader
    dl = ModelDownloader(ctx.obj["config"])

    with console.status("正在搜索..."):
        results = dl.search_models(query, limit)

    table = Table(title=f"? 搜索结果: {query}")
    table.add_column("Repo ID", style="cyan")
    table.add_column("下载量", style="green")
    table.add_column("点赞", style="yellow")
    table.add_column("类型")

    for r in results:
        table.add_row(r["repo_id"], str(r["downloads"]), str(r["likes"]), r["pipeline_tag"])

    console.print(table)


@model.command("delete")
@click.argument("model_path")
@click.pass_context
def model_delete(ctx, model_path):
    """删除本地模型"""
    from .downloader import ModelDownloader
    dl = ModelDownloader(ctx.obj["config"])

    if click.confirm(f"确定要删除 {model_path} 吗？"):
        if dl.delete_model(model_path):
            console.print(f"[green]? 已删除: {model_path}[/green]")
        else:
            console.print(f"[red]? 未找到: {model_path}[/red]")


# ── Inference ────────────────────────────────────────────

@cli.command()
@click.argument("model_path")
@click.option("--temperature", "-t", default=0.7)
@click.option("--max-tokens", "-m", default=2048)
@click.pass_context
def chat(ctx, model_path, temperature, max_tokens):
    """加载模型并进入交互对话"""
    from .runner import create_runner

    config = ctx.obj["config"]

    with console.status("正在加载模型..."):
        runner = create_runner(model_path, config)
        runner.load()

    console.print(f"[green]? 模型已加载: {Path(model_path).name}[/green]")
    console.print("[dim]输入 'quit' 或 'exit' 退出对话[/dim]\n")
    messages = []

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/bold cyan] ")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            break

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        console.print("[bold green]AI:[/bold green] ", end="")
        try:
            response = ""
            for chunk in runner.generate_stream(
                messages, temperature=temperature, max_tokens=max_tokens
            ):
                response += chunk
                console.print(chunk, end="")
            messages.append({"role": "assistant", "content": response})
            console.print()
        except Exception as e:
            console.print(f"\n[red]生成失败: {e}[/red]")

    runner.unload()
    console.print("\n[dim]对话结束[/dim]")


# ── Fine-tune ────────────────────────────────────────────

@cli.command()
@click.argument("model_path")
@click.argument("dataset_path")
@click.option("--method", default="lora", help="微调方法: lora / qlora")
@click.option("--output", "-o", default=None, help="输出目录")
@click.option("--epochs", default=3, help="训练轮数")
@click.option("--batch-size", default=4, help="Batch Size")
@click.option("--lr", default=2e-4, help="学习率")
@click.option("--lora-r", default=16, help="LoRA Rank")
@click.option("--max-seq-len", default=512, help="最大序列长度")
@click.pass_context
def finetune(ctx, model_path, dataset_path, method, output, epochs, batch_size, lr, lora_r, max_seq_len):
    """微调模型"""
    from .finetuner import FineTuner, FineTuneArgs

    config = ctx.obj["config"]
    output_dir = output or str(config.finetune_output_dir / "cli_finetune")

    args = FineTuneArgs(
        model_path=model_path,
        dataset_path=dataset_path,
        output_dir=output_dir,
        method=method,
        lora_r=lora_r,
        learning_rate=lr,
        num_epochs=epochs,
        batch_size=batch_size,
        max_seq_length=max_seq_len,
    )

    def on_progress(info):
        console.print(
            f"  Step {info['step']}/{info['max_steps']} | "
            f"Loss: {info.get('loss', 0):.4f} | "
            f"LR: {info.get('learning_rate', 0):.2e}"
        )

    console.print(Panel(
        f"基座模型: {model_path}\n"
        f"数据集: {dataset_path}\n"
        f"方法: {method}\n"
        f"输出: {output_dir}\n"
        f"轮数: {epochs} | Batch: {batch_size} | LR: {lr}",
        title="? 微调配置",
    ))

    try:
        finetuner = FineTuner(args)
        final_path = finetuner.train(dataset_path, progress_callback=on_progress)
        console.print(f"\n[green]? 微调完成！模型保存至: {final_path}[/green]")
    except Exception as e:
        console.print(f"\n[red]? 微调失败: {e}[/red]")
        raise SystemExit(1)


# ── Upload ───────────────────────────────────────────────

@cli.command()
@click.argument("model_path")
@click.argument("repo_id")
@click.option("--private/--public", default=True, help="私有/公开仓库")
@click.option("--token", default=None, help="HuggingFace Token")
@click.pass_context
def upload(ctx, model_path, repo_id, private, token):
    """上传模型到 HuggingFace Hub"""
    from .exporter import ModelExporter
    exporter = ModelExporter()

    with console.status("正在上传..."):
        try:
            url = exporter.upload_to_huggingface(model_path, repo_id, private, token)
            console.print(f"[green]? 上传成功: {url}[/green]")
        except Exception as e:
            console.print(f"[red]? 上传失败: {e}[/red]")


# ── Web UI ───────────────────────────────────────────────

@cli.command()
@click.option("--port", "-p", default=7860, help="端口号")
@click.option("--share", is_flag=True, help="创建公开分享链接")
@click.pass_context
def ui(ctx, port, share):
    """启动 Web 界面"""
    from .web_ui import launch_ui
    config = ctx.obj["config"]
    console.print(f"[green]? 启动 Web UI: http://localhost:{port}[/green]")
    launch_ui(config, share=share, port=port)


# ── API Server ───────────────────────────────────────────

@cli.command()
@click.option("--host", default=None, help="监听地址，默认读取 config.yaml 的 api.host")
@click.option("--port", "-p", default=None, type=int, help="API 端口号，默认读取 config.yaml 的 api.port")
@click.pass_context
def serve(ctx, host, port):
    """启动 REST API 服务"""
    from .api_server import run_api_server
    config = ctx.obj["config"]
    api_cfg = config.get("api", {})
    host = host or api_cfg.get("host", "127.0.0.1")
    port = port or int(api_cfg.get("port", 8000))
    console.print(f"[green]? 启动 API 服务: http://{host}:{port}[/green]")
    console.print(f"[dim]API 文档: http://localhost:{port}/docs[/dim]")
    run_api_server(config, host=host, port=port)


# ── RAG (Knowledge Base) ────────────────────────────────

@cli.group()
def rag():
    """知识库管理（文档投喂、查询）"""
    pass


@rag.command("ingest")
@click.argument("path")
@click.option("--recursive/--no-recursive", default=True, help="是否递归扫描子目录")
@click.pass_context
def rag_ingest(ctx, path, recursive):
    """投喂文件或目录到知识库"""
    from .rag import RAGPipeline

    config = ctx.obj["config"]
    rag_cfg = config.get("rag", {})
    pipeline = RAGPipeline(
        config,
        embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5"),
        chunk_size=rag_cfg.get("chunk_size", 500),
        chunk_overlap=rag_cfg.get("chunk_overlap", 50),
    )
    pipeline.load()

    p = Path(path)
    with console.status(f"正在处理 {path}..."):
        if p.is_file():
            count = pipeline.ingest_file(str(p))
        elif p.is_dir():
            count = pipeline.ingest_directory(str(p), recursive=recursive)
        else:
            console.print(f"[red]路径不存在: {path}[/red]")
            return

    pipeline.save()
    console.print(f"[green]? 投喂完成: {count} 个文本片段[/green]")
    console.print(f"知识库总计: {pipeline.document_count} 个片段")


@rag.command("status")
@click.pass_context
def rag_status(ctx):
    """查看知识库状态"""
    from .rag import RAGPipeline

    config = ctx.obj["config"]
    rag_cfg = config.get("rag", {})
    pipeline = RAGPipeline(config, embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5"))
    pipeline.load()

    table = Table(title="? 知识库状态")
    table.add_column("项目", style="cyan")
    table.add_column("值", style="green")
    table.add_row("文本片段数", str(pipeline.document_count))
    sources = pipeline.get_ingested_sources()
    table.add_row("来源文件数", str(len(sources)))
    for s in sources:
        table.add_row("  文件", Path(s).name)
    console.print(table)


@rag.command("query")
@click.argument("question")
@click.option("--top-k", "-k", default=5, help="检索片段数")
@click.pass_context
def rag_query(ctx, question, top_k):
    """查询知识库"""
    from .rag import RAGPipeline

    config = ctx.obj["config"]
    rag_cfg = config.get("rag", {})
    pipeline = RAGPipeline(config, embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5"))
    pipeline.load()

    results = pipeline.query(question, top_k=top_k)
    if not results:
        console.print("[yellow]未找到相关文档片段[/yellow]")
        return

    for i, (doc, score) in enumerate(results, 1):
        source = doc.metadata.get("filename", "?")
        console.print(Panel(
            doc.content,
            title=f"[{i}] {source} (相关度: {score:.3f})",
            border_style="cyan",
        ))


@rag.command("clear")
@click.pass_context
def rag_clear_cmd(ctx):
    """清空知识库"""
    from .rag import RAGPipeline

    config = ctx.obj["config"]
    if click.confirm("确定要清空知识库吗？"):
        pipeline = RAGPipeline(config)
        pipeline.clear()
        console.print("[green]? 知识库已清空[/green]")


def main():
    cli()


if __name__ == "__main__":
    main()
