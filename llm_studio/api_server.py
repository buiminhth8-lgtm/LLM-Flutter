"""FastAPI-based REST API server for LLM Studio.

Provides OpenAI-compatible API endpoints for third-party integration.
"""

import asyncio
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from .adapters import AdapterRepository
from .admin import AdminManager
from .api.errors import (
    AUTH_REQUIRED,
    CUDA_OUT_OF_MEMORY,
    GENERATION_CANCELLED,
    GENERATION_TIMEOUT,
    GPU_BUSY,
    INVALID_MESSAGES,
    MODEL_LOAD_BUSY,
    MODEL_NOT_FOUND,
    PERMISSION_DENIED,
    QUEUE_FULL,
    api_error,
    error_payload,
)
from .auth import has_permission, required_permission_for_request
from .benchmarks import BenchmarkConfig, BenchmarkRunner
from .capabilities import get_capabilities
from .chat import ChatMessage as CoreChatMessage
from .chat import InvalidChatMessageError
from .config import Config
from .diagnostics import export_diagnostics
from .downloads import DownloadManager, DownloadRequest, DownloadTaskState
from .execution import run_blocking_io, run_cpu_bound
from .generation import CancellationToken
from .generation.exceptions import (
    CudaOutOfMemoryError,
    GenerationCancelledError,
    GenerationTimeoutError,
)
from .jobs import JobQueue, JobRepository, JobType
from .jobs.exceptions import JobNotImplementedError
from .models import LocalModelRepository
from .models.selection import ModelSelectionError, select_model_for_chat
from .models.storage import layout_from_config
from .rag import RAGPipeline
from .runner import BaseRunner, create_runner
from .runtime.capabilities import detect_runtime_capabilities
from .runtime.concurrency import ModelConcurrencyController, QueueFullError
from .runtime.gpu_scheduler import (
    GpuTaskRequest,
    GpuTaskScheduler,
    GpuTaskTimeoutError,
    GpuTaskType,
)
from .security.uploads import (
    UploadError,
    UploadPolicy,
    save_upload_file_safely,
)
from .storage import CacheManager, collect_disk_usage
from .vision import VisionRunner

# Loaded model runners keyed by model_path
_runners: dict[str, BaseRunner] = {}
_vision_runners: dict[str, VisionRunner] = {}
_rag_pipeline: RAGPipeline | None = None
_config: Config | None = None
_admin: AdminManager | None = None
_concurrency: ModelConcurrencyController | None = None
_model_repository: LocalModelRepository | None = None
_job_repository: JobRepository | None = None
_job_queue: JobQueue | None = None
_download_manager: DownloadManager | None = None
_adapter_repository: AdapterRepository | None = None
_gpu_scheduler: GpuTaskScheduler | None = None
_current_model_id: str | None = None
_runner_model_ids: dict[str, str] = {}


def get_app(config: Config):
    """Create and return the FastAPI application."""
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    from starlette.middleware.base import BaseHTTPMiddleware

    global _config, _rag_pipeline, _admin, _concurrency
    global _model_repository, _job_repository, _job_queue, _download_manager, _adapter_repository, _gpu_scheduler
    _config = config
    layout = layout_from_config(config)
    layout.ensure()
    _admin = AdminManager(layout.root_dir.parent)
    _model_repository = LocalModelRepository(config, layout)
    _job_repository = JobRepository(layout.jobs_dir / "jobs.sqlite")
    _job_queue = JobQueue(_job_repository)
    _download_manager = DownloadManager(config, _job_queue, model_repository=_model_repository)
    _adapter_repository = AdapterRepository(config)
    runtime_cfg = config.runtime
    _concurrency = ModelConcurrencyController(
        max_inference_concurrency=int(runtime_cfg.get("inference_concurrency", 1)),
        max_queue_size=int(runtime_cfg.get("queue_limit", 8)),
    )
    scheduler_cfg = runtime_cfg.get("gpu_scheduler", {})
    _gpu_scheduler = GpuTaskScheduler(
        enabled=bool(scheduler_cfg.get("enabled", True)),
        max_heavy_tasks=int(scheduler_cfg.get("max_heavy_tasks", 1)),
        queue_timeout_seconds=float(scheduler_cfg.get("queue_timeout_seconds", 30)),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _rag_pipeline
        rag_cfg = config.get("rag", {})
        _rag_pipeline = RAGPipeline(
            config,
            embedding_model=rag_cfg.get("embedding_model", "BAAI/bge-small-zh-v1.5"),
            chunk_size=rag_cfg.get("chunk_size", 500),
            chunk_overlap=rag_cfg.get("chunk_overlap", 50),
            device=rag_cfg.get("device", "cpu"),
        )
        _rag_pipeline.load()
        yield
        # Cleanup
        for runner in _runners.values():
            runner.unload()
        for vr in _vision_runners.values():
            vr.unload()
        if _job_queue is not None:
            _job_queue.shutdown(wait=False)

    app = FastAPI(
        title="LLM Studio API",
        description="OpenAI-compatible API for local LLM inference, RAG, and vision.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = f"req-{uuid.uuid4().hex[:12]}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        request_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:12]}")
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload("HTTP_ERROR", str(exc.detail), request_id),
        )

    api_cfg = config.get("api", {})
    allowed_origins = api_cfg.get("allowed_origins", api_cfg.get("cors_origins", []))
    if "*" in allowed_origins:
        raise ValueError('api.allowed_origins cannot include "*" when allow_credentials=True.')

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 鈹€鈹€ Authentication Middleware 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    auth_config = config.get("auth", {})
    auth_enabled = auth_config.get("enabled", False)

    # Paths that skip authentication
    _public_paths = {
        "/health",
        "/ready",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/v1/setup/status",
        "/v1/setup/initialize",
    }
    _admin_paths_prefix = "/admin"

    class AuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if not auth_enabled:
                return await call_next(request)

            path = request.url.path

            # Allow public endpoints
            if path in _public_paths:
                return await call_next(request)

            # Admin pages use session cookie auth, skip header check
            if path.startswith(_admin_paths_prefix):
                return await call_next(request)

            # Allow OPTIONS (CORS preflight)
            if request.method == "OPTIONS":
                return await call_next(request)

            user_id = request.headers.get("X-User-ID", "")
            api_key = request.headers.get("X-API-Key", "")

            # Also support standard Authorization: Bearer header as fallback
            if not api_key:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    api_key = auth_header[7:].strip()

            user = _admin.authenticate(user_id, api_key)
            if not user:
                request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
                return JSONResponse(
                    status_code=401,
                    content=error_payload(
                        AUTH_REQUIRED,
                        "Invalid or missing authentication. Provide X-User-ID and X-API-Key headers.",
                        request_id,
                    ),
                )

            # Attach user info to request state
            request.state.user = user.to_dict()
            permission = required_permission_for_request(request.method, path)
            if permission and not has_permission(user.role, permission):
                request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
                return JSONResponse(
                    status_code=403,
                    content=error_payload(
                        PERMISSION_DENIED,
                        "当前 API Key 没有执行该操作的权限。",
                        request_id,
                    ),
                )
            return await call_next(request)

    app.add_middleware(AuthMiddleware)

    # 鈹€鈹€ Pydantic Models 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    class ChatMessageModel(BaseModel):
        role: str = "user"
        content: str
        name: str | None = None
        tool_call_id: str | None = None

    class ChatRequest(BaseModel):
        model: str = Field(default="auto", description="妯″瀷璺緞锛?auto' 鑷姩閫夋嫨")
        messages: list[ChatMessageModel]
        temperature: float = 0.7
        max_tokens: int = 2048
        top_p: float = 0.9
        stream: bool = False

    class ChatChoice(BaseModel):
        index: int = 0
        message: ChatMessageModel
        finish_reason: str = "stop"

    class Usage(BaseModel):
        prompt_tokens: int = 0
        completion_tokens: int = 0
        total_tokens: int = 0

    class ChatResponse(BaseModel):
        id: str
        object: str = "chat.completion"
        created: int
        model: str
        choices: list[ChatChoice]
        usage: Usage

    class SetupInitializeRequest(BaseModel):
        admin_password: str
        display_name: str = "Admin"

    class ModelInfo(BaseModel):
        id: str
        object: str = "model"
        owned_by: str = "local"

    class ModelListResponse(BaseModel):
        object: str = "list"
        data: list[ModelInfo]

    class RAGIngestRequest(BaseModel):
        file_path: str | None = None
        directory_path: str | None = None
        recursive: bool = True

    class RAGQueryRequest(BaseModel):
        question: str
        top_k: int = 5
        model: str | None = None
        temperature: float = 0.7
        max_tokens: int = 2048

    class VisionRequest(BaseModel):
        model: str = Field(..., description="瑙嗚妯″瀷璺緞")
        image_path: str = Field(..., description="鍥剧墖鏂囦欢璺緞")
        prompt: str = "Please describe this image."
        max_tokens: int = 1024
        temperature: float = 0.7

    class LoadModelRequest(BaseModel):
        model: str = Field(..., description="妯″瀷璺緞")
        model_type: str = "text"  # "text" or "vision"
        strategy: str = "auto"

    class RegisterModelRequest(BaseModel):
        path: str

    class DownloadModelRequest(BaseModel):
        repo_id: str
        revision: str | None = None
        allow_patterns: list[str] | None = None
        ignore_patterns: list[str] | None = None
        local_name: str | None = None
        local_files_only: bool = False

    class AdapterPathRequest(BaseModel):
        path: str

    class AdapterActionRequest(BaseModel):
        model: str = "auto"
        adapter_name: str | None = None

    class BenchmarkRequest(BaseModel):
        model_id: str
        adapter_id: str | None = None
        prompt_set: str = "default"
        warmup_runs: int = 1
        measured_runs: int = 3
        max_new_tokens: int = 128
        context_lengths: list[int] = Field(default_factory=lambda: [512, 2048])

    class StorageCleanupRequest(BaseModel):
        categories: list[str] | None = None

    # 鈹€鈹€ Helper Functions 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    def _gpu_request(task_type: GpuTaskType, owner: str, request_id: str | None = None) -> GpuTaskRequest:
        scheduler_cfg = config.runtime.get("gpu_scheduler", {})
        return GpuTaskRequest(
            task_type=task_type,
            owner=owner,
            request_id=request_id,
            timeout_seconds=float(scheduler_cfg.get("queue_timeout_seconds", 30)),
        )

    def _upload_policy(kind: str) -> UploadPolicy:
        upload_cfg = config.get("uploads", {})
        temp_dir = Path(upload_cfg.get("temp_dir", "./data/uploads"))
        if kind == "document":
            max_mb = int(upload_cfg.get("max_document_size_mb", 50))
            extensions = tuple(upload_cfg.get("allowed_document_extensions", [".txt", ".md", ".pdf", ".docx"]))
            destination = temp_dir / "documents"
        elif kind == "image":
            max_mb = int(upload_cfg.get("max_image_size_mb", 20))
            extensions = tuple(upload_cfg.get("allowed_image_extensions", [".png", ".jpg", ".jpeg", ".webp"]))
            destination = temp_dir / "images"
        else:
            raise ValueError(f"Unsupported upload kind: {kind}")
        return UploadPolicy(
            max_size_bytes=max_mb * 1024 * 1024,
            allowed_extensions=extensions,
            allowed_mime_types=None,
            destination_dir=destination,
        )

    def _raise_upload_error(exc: UploadError, request_id: str):
        raise api_error(exc.status_code, exc.code, str(exc), request_id) from exc

    def _select_repository_model(model: str | None, request_id: str):
        assert _model_repository is not None
        caps = detect_runtime_capabilities(run_bnb_probe=False)
        try:
            return select_model_for_chat(model, _model_repository, caps)
        except ModelSelectionError as exc:
            raise api_error(404, MODEL_NOT_FOUND, str(exc), request_id) from exc

    async def _get_or_load_runner(model_id: str | None, request_id: str) -> tuple[str, BaseRunner]:
        """Get runner through LocalModelRepository, auto-loading when needed."""
        global _current_model_id
        selected = _select_repository_model(model_id, request_id)
        model_path = str(selected.path)

        if model_path not in _runners:
            # Auto-load: compatible with LM Studio behavior
            try:
                assert _concurrency is not None and _gpu_scheduler is not None
                async with _concurrency.model_load():
                    if model_path in _runners:
                        _current_model_id = selected.id
                        _runner_model_ids[model_path] = selected.id
                        return selected.id, _runners[model_path]
                    runner = create_runner(model_path, config)
                    async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.MODEL_LOAD, "model-load", request_id)):
                        await run_blocking_io(runner.load)
                    _runners[model_path] = runner
                    _runner_model_ids[model_path] = selected.id
                    _current_model_id = selected.id
            except GpuTaskTimeoutError as e:
                raise api_error(409, MODEL_LOAD_BUSY, str(e), request_id) from e
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load model '{selected.display_name}': {e}",
                ) from e
        else:
            _runner_model_ids[model_path] = selected.id
            _current_model_id = selected.id
        return selected.id, _runners[model_path]

    def _get_vision_runner(model_path: str) -> VisionRunner:
        if model_path not in _vision_runners:
            raise HTTPException(
                status_code=400,
                detail=f"Vision model not loaded: {model_path}. Call POST /v1/models/load first.",
            )
        return _vision_runners[model_path]

    async def _load_text_model(model_id: str, request_id: str) -> dict:
        global _current_model_id
        selected = _select_repository_model(model_id, request_id)
        model_path = str(selected.path)
        if model_path not in _runners:
            assert _concurrency is not None and _gpu_scheduler is not None
            async with _concurrency.model_load():
                if model_path not in _runners:
                    runner = create_runner(model_path, config)
                    async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.MODEL_LOAD, "model-load", request_id)):
                        await run_blocking_io(runner.load)
                    _runners[model_path] = runner
        _runner_model_ids[model_path] = selected.id
        _current_model_id = selected.id
        runner = _runners[model_path]
        policy = getattr(runner, "load_policy", None)
        return {
            "model_id": selected.id,
            "status": "loaded",
            "backend": type(runner).__name__,
            "dtype": getattr(policy, "dtype", None),
            "quantization": getattr(policy, "quantization", None),
        }

    # 鈹€鈹€ Endpoints: Models 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    @app.get("/v1/models")
    async def list_models():
        """List local and loaded models."""
        assert _model_repository is not None
        models = [model.to_dict() for model in _model_repository.list_models(refresh=False)]
        for path in _runners:
            models.append({"id": path, "path": path, "status": "loaded", "format": "runtime"})
        for path in _vision_runners:
            models.append({"id": path, "path": path, "status": "vision-loaded", "format": "runtime"})
        return {"object": "list", "data": models}

    @app.post("/v1/models/scan")
    async def scan_models():
        assert _job_queue is not None and _model_repository is not None

        def handler(job, update, cancel):
            update(0.1, "开始扫描本地模型。")
            models = _model_repository.scan()
            update(1.0, f"扫描完成: {len(models)} 个模型。")

        job = _job_queue.submit(JobType.MODEL_SCAN.value, {}, handler)
        return {"job_id": job.id}

    @app.post("/v1/models/register")
    async def register_model(req: RegisterModelRequest):
        assert _model_repository is not None
        model = _model_repository.register_external(req.path)
        return {"status": "ok", "model": model.to_dict()}

    @app.delete("/v1/models/{model_id}")
    async def delete_model(model_id: str, confirm: bool = False):
        assert _model_repository is not None
        target = _model_repository.move_to_trash(model_id, confirm=confirm)
        return {"status": "moved_to_trash", "trash_path": str(target)}

    @app.post("/v1/models/load")
    async def load_model(req: LoadModelRequest):
        """Load a model by repository id, preserving the legacy body endpoint."""
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        if req.model_type == "vision":
            if req.model not in _vision_runners:
                vr = VisionRunner(req.model, config)
                assert _gpu_scheduler is not None
                try:
                    async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.MODEL_LOAD, "vision-load", request_id)):
                        await run_blocking_io(vr.load)
                except GpuTaskTimeoutError as e:
                    raise api_error(409, MODEL_LOAD_BUSY, str(e), request_id) from e
                _vision_runners[req.model] = vr
            return {"status": "ok", "model": req.model, "type": "vision"}
        return await _load_text_model(req.model, request_id)

    @app.post("/v1/models/{model_id}/load")
    async def load_model_by_id(model_id: str):
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        return await _load_text_model(model_id, request_id)

    @app.get("/v1/models/current")
    async def current_model():
        if not _current_model_id:
            return {"loaded": False}
        assert _model_repository is not None
        try:
            model = _model_repository.get(_current_model_id)
        except Exception:
            return {"loaded": False}
        model_path = str(model.path)
        runner = _runners.get(model_path)
        policy = getattr(runner, "load_policy", None) if runner else None
        return {
            "loaded": runner is not None,
            "model_id": model.id,
            "display_name": model.display_name,
            "backend": type(runner).__name__ if runner else None,
            "dtype": getattr(policy, "dtype", None),
            "quantization": getattr(policy, "quantization", None),
            "loaded_adapters": list(runner.list_loaded_adapters()) if runner and hasattr(runner, "list_loaded_adapters") else [],
        }

    @app.post("/v1/models/unload")
    async def unload_model(req: LoadModelRequest):
        """Unload the current or requested model."""
        global _current_model_id
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        assert _gpu_scheduler is not None and _concurrency is not None
        try:
            async with _concurrency.model_unload():
                async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.MODEL_UNLOAD, "model-unload", request_id)):
                    if req.model_type == "vision" and req.model in _vision_runners:
                        await run_blocking_io(_vision_runners[req.model].unload)
                        del _vision_runners[req.model]
                    else:
                        model_path = req.model
                        selected_id = req.model
                        try:
                            selected = _select_repository_model(req.model, request_id)
                            model_path = str(selected.path)
                            selected_id = selected.id
                        except Exception:
                            pass
                        if model_path in _runners:
                            await run_blocking_io(_runners[model_path].unload)
                            del _runners[model_path]
                            _runner_model_ids.pop(model_path, None)
                        if _current_model_id == selected_id or not _runners:
                            _current_model_id = None
        except GpuTaskTimeoutError as e:
            raise api_error(409, GPU_BUSY, str(e), request_id) from e
        return {"status": "ok", "model": req.model}

    @app.post("/v1/downloads")
    async def create_download(req: DownloadModelRequest):
        assert _download_manager is not None
        job = _download_manager.create_download(
            DownloadRequest(
                repo_id=req.repo_id,
                revision=req.revision,
                allow_patterns=tuple(req.allow_patterns) if req.allow_patterns else None,
                ignore_patterns=tuple(req.ignore_patterns) if req.ignore_patterns else None,
                local_name=req.local_name,
                token=None,
                local_files_only=req.local_files_only,
            )
        )
        return {"job_id": job.id}

    @app.get("/v1/downloads")
    async def list_downloads():
        assert _job_repository is not None
        return {
            "data": [
                DownloadTaskState.from_job(job).to_dict()
                for job in _job_repository.list(limit=100)
                if job.type == JobType.MODEL_DOWNLOAD.value
            ]
        }

    @app.get("/v1/downloads/{job_id}")
    async def get_download(job_id: str):
        assert _job_repository is not None
        job = _job_repository.get(job_id)
        return DownloadTaskState.from_job(job).to_dict()

    @app.post("/v1/downloads/{job_id}/cancel")
    async def cancel_download(job_id: str):
        assert _download_manager is not None
        job = _download_manager.cancel_job(job_id)
        data = DownloadTaskState.from_job(job).to_dict()
        data["cancel_semantics"] = "取消请求已提交；当前网络传输步骤可能结束后才会停止，重试会复用 Hugging Face 缓存。"
        return data

    @app.post("/v1/downloads/{job_id}/retry")
    async def retry_download(job_id: str):
        assert _download_manager is not None and _job_repository is not None
        return {
            "job_id": _download_manager.retry_interrupted(_job_repository.get(job_id)).id,
            "resume_supported": True,
            "message": "Retry reuses the Hugging Face cache; strict pause/resume is not claimed.",
        }

    @app.get("/v1/jobs")
    async def list_jobs(limit: int = 50, offset: int = 0):
        assert _job_repository is not None
        return {"data": [job.to_dict() for job in _job_repository.list(limit=limit, offset=offset)]}

    @app.get("/v1/jobs/{job_id}")
    async def get_job(job_id: str):
        assert _job_repository is not None
        return _job_repository.get(job_id).to_dict()

    @app.post("/v1/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str):
        assert _job_queue is not None
        return _job_queue.cancel(job_id).to_dict()

    @app.get("/v1/adapters")
    async def list_adapters():
        assert _adapter_repository is not None
        return {"data": [adapter.to_dict() for adapter in _adapter_repository.list()]}

    @app.post("/v1/adapters/scan")
    async def scan_adapters():
        assert _adapter_repository is not None
        adapters = await run_blocking_io(_adapter_repository.list)
        return {"data": [adapter.to_dict() for adapter in adapters]}

    @app.post("/v1/adapters/register")
    async def register_adapter(req: AdapterPathRequest):
        assert _adapter_repository is not None
        return _adapter_repository.register_path(req.path).to_dict()

    @app.post("/v1/adapters/{adapter_id}/load")
    async def load_adapter(adapter_id: str, req: AdapterActionRequest):
        assert _adapter_repository is not None
        _, runner = await _get_or_load_runner(req.model, f"req-{uuid.uuid4().hex[:12]}")
        adapter = _adapter_repository.get(adapter_id)
        name = await asyncio.to_thread(runner.load_adapter, adapter, req.adapter_name)
        return {"status": "ok", "adapter_name": name, "loaded_adapters": runner.list_loaded_adapters()}

    @app.post("/v1/adapters/{adapter_id}/activate")
    async def activate_adapter(adapter_id: str, req: AdapterActionRequest):
        assert _adapter_repository is not None
        _, runner = await _get_or_load_runner(req.model, f"req-{uuid.uuid4().hex[:12]}")
        adapter = _adapter_repository.get(adapter_id)
        await run_blocking_io(runner.activate_adapter, req.adapter_name or adapter.name)
        return {"status": "ok", "active_adapter": req.adapter_name or adapter.name}

    @app.post("/v1/adapters/{adapter_id}/deactivate")
    async def deactivate_adapter(adapter_id: str, req: AdapterActionRequest):
        _, runner = await _get_or_load_runner(req.model, f"req-{uuid.uuid4().hex[:12]}")
        await run_blocking_io(runner.deactivate_adapter)
        return {"status": "ok", "active_adapter": None, "loaded_adapters": runner.list_loaded_adapters()}

    @app.post("/v1/adapters/{adapter_id}/unload")
    async def unload_adapter(adapter_id: str, req: AdapterActionRequest):
        assert _adapter_repository is not None
        _, runner = await _get_or_load_runner(req.model, f"req-{uuid.uuid4().hex[:12]}")
        adapter = _adapter_repository.get(adapter_id)
        name = req.adapter_name or adapter.name
        await run_blocking_io(runner.unload_adapter, name)
        return {"status": "ok", "unloaded_adapter": name, "loaded_adapters": runner.list_loaded_adapters()}

    @app.post("/v1/adapters/{adapter_id}/merge")
    async def merge_adapter(adapter_id: str, req: AdapterActionRequest):
        assert _job_queue is not None
        job = _job_queue.submit(
            JobType.LORA_MERGE.value,
            {"adapter_id": adapter_id, "model": req.model, "adapter_name": req.adapter_name},
            lambda job, update, cancel: (_ for _ in ()).throw(
                JobNotImplementedError("LoRA 合并后台执行器尚未实现，未修改基础模型。")
            ),
        )
        return {"job_id": job.id}

    @app.post("/v1/benchmarks")
    async def create_benchmark(req: BenchmarkRequest):
        assert _job_queue is not None

        def handler(job, update, cancel):
            update(0.05, "开始 Benchmark。")
            assert _gpu_scheduler is not None
            with _gpu_scheduler.acquire_sync(_gpu_request(GpuTaskType.BENCHMARK, "benchmark", job.id)):
                bench = BenchmarkRunner(config, lambda model_id: create_runner(model_id, config))
                try:
                    bench.run(
                        BenchmarkConfig(
                            model_id=req.model_id,
                            adapter_id=req.adapter_id,
                            prompt_set=req.prompt_set,
                            warmup_runs=req.warmup_runs,
                            measured_runs=req.measured_runs,
                            max_new_tokens=req.max_new_tokens,
                            context_lengths=tuple(req.context_lengths),
                        )
                    )
                except RuntimeError as exc:
                    if "out of memory" in str(exc).lower():
                        raise RuntimeError(f"BENCHMARK_OOM: {exc}") from exc
                    raise
            update(1.0, "Benchmark 完成。")

        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        job = _job_queue.submit(JobType.BENCHMARK.value, payload, handler)
        return {"job_id": job.id}

    @app.get("/v1/benchmarks")
    async def list_benchmarks():
        from .benchmarks.repository import BenchmarkRepository

        data = await run_blocking_io(BenchmarkRepository(config).list)
        return {"data": data}

    @app.get("/v1/benchmarks/{benchmark_id}")
    async def get_benchmark(benchmark_id: str):
        from .benchmarks.repository import BenchmarkRepository

        return await run_blocking_io(BenchmarkRepository(config).get, benchmark_id)

    @app.delete("/v1/benchmarks/{benchmark_id}")
    async def delete_benchmark(benchmark_id: str):
        from .benchmarks.repository import BenchmarkRepository

        deleted = await run_blocking_io(BenchmarkRepository(config).delete, benchmark_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Benchmark not found.")
        return {"status": "deleted", "id": benchmark_id}

    @app.get("/v1/storage")
    async def storage_status():
        items = await run_blocking_io(collect_disk_usage, config)
        return {"data": [item.to_dict() for item in items]}

    @app.post("/v1/storage/cleanup/preview")
    async def cleanup_storage_preview(req: StorageCleanupRequest | None = None):
        manager = CacheManager(config)
        categories = set(req.categories) if req and req.categories else None
        items = await run_blocking_io(manager.preview_cleanup, categories)
        return {
            "items": [item.to_dict() for item in items],
            "total_size_bytes": sum(item.size_bytes for item in items),
        }

    @app.post("/v1/storage/cleanup")
    async def cleanup_storage(req: StorageCleanupRequest | None = None):
        manager = CacheManager(config)
        categories = set(req.categories) if req and req.categories else None
        items = await run_blocking_io(manager.preview_cleanup, categories)
        return await run_blocking_io(manager.cleanup_preview_items, items)

    @app.post("/v1/diagnostics/export")
    async def diagnostics_export():
        path = await run_blocking_io(export_diagnostics, config)
        return {"status": "ok", "path": str(path)}

    # 鈹€鈹€ Endpoints: Chat (OpenAI-compatible) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatRequest, request: Request):
        """OpenAI-compatible chat completions endpoint."""
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        raw_messages = [
            msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
            for msg in req.messages
        ]
        try:
            messages = [CoreChatMessage.from_dict(item) for item in raw_messages]
        except InvalidChatMessageError as exc:
            raise api_error(400, INVALID_MESSAGES, str(exc), request_id) from exc
        if not messages:
            raise api_error(400, INVALID_MESSAGES, "messages 不能为空。", request_id)
        if not any(message.role == "user" for message in messages):
            raise api_error(400, INVALID_MESSAGES, "至少需要一条 user 消息。", request_id)
        if messages[-1].role not in {"user", "tool"}:
            raise api_error(400, INVALID_MESSAGES, "至少需要一条 user 消息。", request_id)

        # 鈹€鈹€ Streaming mode (SSE) 鈹€鈹€
        resolved_model_id, runner = await _get_or_load_runner(req.model, request_id)

        if req.stream:
            from fastapi.responses import StreamingResponse

            async def event_stream():
                chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                created = int(time.time())
                try:
                    assert _concurrency is not None and _gpu_scheduler is not None
                    cancellation = CancellationToken()
                    async with _concurrency.inference(
                        wait_timeout_seconds=float(config.runtime.get("request_timeout_seconds", 300))
                    ):
                        async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.INFERENCE, "chat-stream", request_id)):
                            for chunk_text in runner.generate_stream(
                                messages,
                                cancellation_token=cancellation,
                                temperature=req.temperature,
                                max_tokens=req.max_tokens,
                                top_p=req.top_p,
                            ):
                                if await request.is_disconnected():
                                    cancellation.cancel()
                                    break
                                chunk = {
                                    "id": chat_id,
                                    "object": "chat.completion.chunk",
                                    "created": created,
                                    "model": resolved_model_id,
                                    "choices": [{
                                        "index": 0,
                                        "delta": {"content": chunk_text},
                                        "finish_reason": None,
                                    }],
                                }
                                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                                await asyncio.sleep(0)
                except QueueFullError as e:
                    yield f"data: {json.dumps(error_payload(QUEUE_FULL, str(e), request_id), ensure_ascii=False)}\n\n"
                    return
                except GpuTaskTimeoutError as e:
                    yield f"data: {json.dumps(error_payload(GPU_BUSY, str(e), request_id), ensure_ascii=False)}\n\n"
                    return
                except GenerationTimeoutError as e:
                    yield f"data: {json.dumps(error_payload(GENERATION_TIMEOUT, str(e), request_id), ensure_ascii=False)}\n\n"
                    return
                except GenerationCancelledError as e:
                    yield f"data: {json.dumps(error_payload(GENERATION_CANCELLED, str(e), request_id), ensure_ascii=False)}\n\n"
                    return
                except CudaOutOfMemoryError as e:
                    yield f"data: {json.dumps(error_payload(CUDA_OUT_OF_MEMORY, str(e), request_id), ensure_ascii=False)}\n\n"
                    return
                except Exception:
                    yield f"data: {json.dumps(error_payload('GENERATION_ERROR', '生成失败。', request_id), ensure_ascii=False)}\n\n"
                    return

                # Final chunk with finish_reason
                done_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": resolved_model_id,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }],
                }
                yield f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # 鈹€鈹€ Non-streaming mode 鈹€鈹€
        try:
            assert _concurrency is not None and _gpu_scheduler is not None
            async with _concurrency.inference(
                wait_timeout_seconds=float(config.runtime.get("request_timeout_seconds", 300))
            ):
                async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.INFERENCE, "chat", request_id)):
                    response_text = await run_blocking_io(
                        runner.generate,
                        messages,
                        temperature=req.temperature,
                        max_tokens=req.max_tokens,
                        top_p=req.top_p,
                    )
        except QueueFullError as e:
            raise api_error(429, QUEUE_FULL, str(e), request_id) from e
        except GpuTaskTimeoutError as e:
            raise api_error(409, GPU_BUSY, str(e), request_id) from e
        except GenerationTimeoutError as e:
            raise api_error(504, GENERATION_TIMEOUT, str(e), request_id) from e
        except GenerationCancelledError as e:
            raise api_error(499, GENERATION_CANCELLED, str(e), request_id) from e
        except CudaOutOfMemoryError as e:
            raise api_error(507, CUDA_OUT_OF_MEMORY, str(e), request_id) from e
        except Exception as e:
            raise api_error(500, "GENERATION_ERROR", "生成失败。", request_id) from e

        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=resolved_model_id,
            choices=[
                ChatChoice(
                    message=ChatMessageModel(role="assistant", content=response_text)
                )
            ],
            usage=Usage(),
        )

    # 鈹€鈹€ Endpoints: RAG 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    @app.post("/v1/rag/ingest")
    async def rag_ingest(req: RAGIngestRequest, sync: bool = False):
        """RAG endpoint."""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        def ingest() -> dict:
            total_chunks = 0
            if req.file_path:
                total_chunks = total_chunks + _rag_pipeline.ingest_file(req.file_path)
            if req.directory_path:
                total_chunks = total_chunks + _rag_pipeline.ingest_directory(
                    req.directory_path, recursive=req.recursive
                )
            _rag_pipeline.save()
            return {
                "status": "ok",
                "chunks_added": total_chunks,
                "total_chunks": _rag_pipeline.document_count,
            }

        if sync:
            return await run_cpu_bound(ingest)

        assert _job_queue is not None
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        job = _job_queue.submit(JobType.RAG_REBUILD.value, payload, lambda job, update, cancel: ingest())
        return {"job_id": job.id}

    @app.post("/v1/rag/ingest/upload")
    async def rag_ingest_upload(file: Annotated[UploadFile, File(...)], sync: bool = False):
        """RAG endpoint."""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        request_id = f"req-{uuid.uuid4().hex[:12]}"
        try:
            saved = await save_upload_file_safely(file, _upload_policy("document"))
        except UploadError as exc:
            _raise_upload_error(exc, request_id)

        def ingest_saved() -> dict:
            chunks = _rag_pipeline.ingest_file(str(saved.path))
            _rag_pipeline.save()
            return {
                "status": "ok",
                "filename": saved.original_filename,
                "stored_filename": saved.safe_filename,
                "chunks_added": chunks,
                "total_chunks": _rag_pipeline.document_count,
            }

        if sync:
            return await run_cpu_bound(ingest_saved)

        assert _job_queue is not None
        job = _job_queue.submit(
            JobType.RAG_REBUILD.value,
            {"file_path": str(saved.path), "filename": saved.original_filename},
            lambda job, update, cancel: ingest_saved(),
        )
        return {"job_id": job.id, "filename": saved.original_filename}

    @app.post("/v1/rag/query")
    async def rag_query(req: RAGQueryRequest):
        """RAG endpoint."""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        # Retrieve relevant docs
        results = await run_cpu_bound(_rag_pipeline.query, req.question, top_k=req.top_k)

        context_docs = [
            {
                "content": doc.content,
                "source": doc.metadata.get("filename", "unknown"),
                "score": round(score, 4),
            }
            for doc, score in results
        ]

        # If a model is specified, generate a RAG-enhanced answer
        answer = None
        if req.model:
            resolved_model_id, runner = await _get_or_load_runner(req.model, f"req-{uuid.uuid4().hex[:12]}")
            rag_prompt = _rag_pipeline.build_rag_prompt(req.question, top_k=req.top_k)
            assert _gpu_scheduler is not None
            async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.INFERENCE, "rag-query", resolved_model_id)):
                answer = await run_blocking_io(
                    runner.generate,
                    rag_prompt,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                )

        return {
            "question": req.question,
            "retrieved_documents": context_docs,
            "answer": answer,
        }

    @app.get("/v1/rag/status")
    async def rag_status():
        """RAG endpoint."""
        if _rag_pipeline is None:
            return {"status": "not_initialized"}
        return {
            "status": "ok",
            "document_count": _rag_pipeline.document_count,
            "sources": _rag_pipeline.get_ingested_sources(),
        }

    @app.post("/v1/rag/clear")
    async def rag_clear():
        """Clear the RAG index."""
        if _rag_pipeline:
            await run_blocking_io(_rag_pipeline.clear)
        return {"status": "ok"}

    # 鈹€鈹€ Endpoints: Vision 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    @app.post("/v1/vision/analyze")
    async def vision_analyze(req: VisionRequest):
        """Analyze an image path with a loaded vision model."""
        vr = _get_vision_runner(req.model)
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        try:
            assert _gpu_scheduler is not None
            async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.VISION, "vision-analyze", request_id)):
                response = await run_blocking_io(
                    vr.analyze_image,
                    req.image_path,
                    prompt=req.prompt,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                )
            return {"image": req.image_path, "prompt": req.prompt, "response": response}
        except GpuTaskTimeoutError as e:
            raise api_error(409, GPU_BUSY, str(e), request_id) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.post("/v1/vision/analyze/upload")
    async def vision_analyze_upload(
        file: Annotated[UploadFile, File(...)],
        model: Annotated[str, Form(...)],
        prompt: Annotated[str, Form()] = "Please describe this image.",
        max_tokens: Annotated[int, Form()] = 1024,
    ):
        """Safely upload an image and analyze it with a loaded vision model."""
        vr = _get_vision_runner(model)
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        try:
            saved = await save_upload_file_safely(file, _upload_policy("image"))
        except UploadError as exc:
            _raise_upload_error(exc, request_id)

        try:
            assert _gpu_scheduler is not None
            async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.VISION, "vision-upload", request_id)):
                response = await run_blocking_io(
                    vr.analyze_image,
                    str(saved.path),
                    prompt=prompt,
                    max_tokens=max_tokens,
                )
            return {"filename": saved.original_filename, "prompt": prompt, "response": response}
        except GpuTaskTimeoutError as e:
            raise api_error(409, GPU_BUSY, str(e), request_id) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        finally:
            saved.path.unlink(missing_ok=True)

    @app.post("/v1/vision/ocr")
    async def vision_ocr(
        file: Annotated[UploadFile, File(...)],
        model: Annotated[str, Form(...)],
    ):
        """Safely upload an image and run OCR."""
        vr = _get_vision_runner(model)
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        try:
            saved = await save_upload_file_safely(file, _upload_policy("image"))
        except UploadError as exc:
            _raise_upload_error(exc, request_id)

        try:
            assert _gpu_scheduler is not None
            async with _gpu_scheduler.acquire(_gpu_request(GpuTaskType.VISION, "vision-ocr", request_id)):
                text = await run_blocking_io(vr.ocr_image, str(saved.path))
            return {"filename": saved.original_filename, "text": text}
        except GpuTaskTimeoutError as e:
            raise api_error(409, GPU_BUSY, str(e), request_id) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        finally:
            saved.path.unlink(missing_ok=True)

    # 鈹€鈹€ Health Check 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def ready():
        return {
            "status": "ok",
            "config_loaded": _config is not None,
            "model_manager_available": _concurrency is not None,
            "model_loading": _concurrency.is_loading_locked if _concurrency else False,
            "loaded_text_models": list(_runners.keys()),
            "loaded_vision_models": list(_vision_runners.keys()),
            "rag_documents": _rag_pipeline.document_count if _rag_pipeline else 0,
        }

    @app.get("/v1/setup/status")
    async def setup_status():
        assert _admin is not None
        return {
            "initialized": _admin.initialized,
            "auth_enabled": bool(auth_enabled),
            "requires_setup": bool(auth_enabled and not _admin.initialized),
        }

    @app.post("/v1/setup/initialize")
    async def setup_initialize(req: SetupInitializeRequest):
        assert _admin is not None
        if _admin.initialized:
            raise HTTPException(status_code=409, detail="LLM Studio 已初始化。")
        try:
            admin = _admin.initialize(req.admin_password, req.display_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="原密码错误。") from exc
        return {"user_id": admin.user_id, "api_key": admin.plain_api_key}

    @app.get("/v1/gpu/scheduler")
    async def gpu_scheduler_status():
        if _gpu_scheduler is None:
            return {"enabled": False, "max_heavy_tasks": 0, "running": [], "queued_count": 0}
        return _gpu_scheduler.snapshot().to_dict()

    @app.get("/v1/capabilities")
    async def capabilities_status():
        return {"capabilities": [capability.to_dict() for capability in get_capabilities()]}

    @app.get("/v1/runtime")
    async def runtime_status():
        caps = detect_runtime_capabilities(run_bnb_probe=False)
        current_path = None
        for path, model_id in _runner_model_ids.items():
            if model_id == _current_model_id:
                current_path = path
                break
        runner = _runners.get(current_path) if current_path else None
        policy = getattr(runner, "load_policy", None) if runner else None
        return {
            "python_version": caps.python_version,
            "torch_version": caps.torch_version,
            "cuda_runtime": caps.cuda_runtime,
            "cuda_available": caps.cuda_available,
            "gpu_name": caps.gpu_name,
            "total_vram_bytes": caps.total_vram_bytes,
            "bf16_supported": caps.bf16_supported,
            "current_model": _current_model_id,
            "backend": type(runner).__name__ if runner else None,
            "quantization": getattr(policy, "quantization", None),
            "queue_length": _concurrency.queue_size if _concurrency else 0,
            "inference_concurrency": _concurrency.max_inference_concurrency if _concurrency else None,
        }

    # 鈹€鈹€ Admin Backend 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

    # Simple session token store (in-memory, cleared on restart)
    _admin_sessions: set[str] = set()

    class AdminLoginRequest(BaseModel):
        password: str

    class AdminCreateUserRequest(BaseModel):
        user_id: str
        role: str = "user"
        note: str = ""

    class AdminUpdateUserRequest(BaseModel):
        role: str | None = None
        note: str | None = None

    class AdminChangePasswordRequest(BaseModel):
        old_password: str
        new_password: str

    def _verify_admin_session(request: Request):
        """Verify admin session token from cookie."""
        token = request.cookies.get("admin_token", "")
        if token not in _admin_sessions:
            raise HTTPException(status_code=401, detail="璇峰厛鐧诲綍绠＄悊鍚庡彴")

    @app.post("/admin/api/login")
    async def admin_login(request: Request, req: AdminLoginRequest):
        """API endpoint."""
        if not _admin.verify_admin_password(req.password):
            raise HTTPException(status_code=401, detail="瀵嗙爜閿欒")
        token = secrets.token_hex(32)
        _admin_sessions.add(token)
        response = JSONResponse({"status": "ok"})
        response.set_cookie(
            "admin_token", token,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="strict",
            max_age=86400,
        )
        return response

    @app.post("/admin/api/logout")
    async def admin_logout(request: Request):
        token = request.cookies.get("admin_token", "")
        _admin_sessions.discard(token)
        response = JSONResponse({"status": "ok"})
        response.delete_cookie("admin_token")
        return response

    @app.get("/admin/api/users")
    async def admin_list_users(request: Request):
        _verify_admin_session(request)
        return {"users": _admin.list_users()}

    @app.post("/admin/api/users")
    async def admin_create_user(request: Request, req: AdminCreateUserRequest):
        _verify_admin_session(request)
        try:
            user = _admin.create_user(req.user_id, role=req.role, note=req.note)
            return {"status": "ok", "user": user.to_dict(include_secret=True)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="原密码错误。") from exc

    @app.delete("/admin/api/users/{user_id}")
    async def admin_delete_user(request: Request, user_id: str):
        _verify_admin_session(request)
        if not _admin.delete_user(user_id):
            raise HTTPException(status_code=404, detail="用户不存在。")
        return {"status": "ok"}

    @app.put("/admin/api/users/{user_id}")
    async def admin_update_user(request: Request, user_id: str, req: AdminUpdateUserRequest):
        _verify_admin_session(request)
        if not _admin.update_user(user_id, role=req.role, note=req.note):
            raise HTTPException(status_code=404, detail="用户不存在。")
        return {"status": "ok"}

    @app.post("/admin/api/users/{user_id}/toggle")
    async def admin_toggle_user(request: Request, user_id: str):
        _verify_admin_session(request)
        result = _admin.toggle_user(user_id)
        if result is None:
            raise HTTPException(status_code=404, detail="用户不存在。")
        return {"status": "ok", "enabled": result}

    @app.post("/admin/api/users/{user_id}/regenerate")
    async def admin_regenerate_key(request: Request, user_id: str):
        _verify_admin_session(request)
        new_key = _admin.regenerate_key(user_id)
        if not new_key:
            raise HTTPException(status_code=404, detail="用户不存在。")
        return {"status": "ok", "api_key": new_key}

    @app.get("/admin/api/users/{user_id}/key")
    async def admin_get_full_key(request: Request, user_id: str):
        _verify_admin_session(request)
        key = _admin.get_full_key(user_id)
        if not key:
            raise HTTPException(
                status_code=410,
                detail="API Key 只在创建或重置时显示一次，无法再次读取。",
            )
        return {"api_key": key}

    @app.post("/admin/api/change-password")
    async def admin_change_password(request: Request, req: AdminChangePasswordRequest):
        _verify_admin_session(request)
        if not _admin.change_admin_password(req.old_password, req.new_password):
            raise HTTPException(status_code=400, detail="原密码错误。")
        return {"status": "ok"}

    # 鈹€鈹€ /api/v1 alias (RemoteAssistant compatibility) 鈹€鈹€鈹€鈹€鈹€鈹€
    # RemoteAssistant llmstudio preset uses /api/v1/* paths
    from fastapi import APIRouter

    api_v1_router = APIRouter(prefix="/api/v1")

    @api_v1_router.get("/models")
    async def api_v1_list_models():
        return await list_models()

    @api_v1_router.post("/models/load")
    async def api_v1_load_model(req: LoadModelRequest):
        return await load_model(req)

    @api_v1_router.post("/models/unload")
    async def api_v1_unload_model(req: LoadModelRequest):
        return await unload_model(req)

    @api_v1_router.post("/chat/completions")
    async def api_v1_chat(req: ChatRequest, request: Request):
        return await chat_completions(req, request)

    app.include_router(api_v1_router)

    return app


def run_api_server(config: Config, host: str | None = None, port: int | None = None):
    """Start the API server."""
    import uvicorn
    api_cfg = config.get("api", {})
    host = host or api_cfg.get("host", "127.0.0.1")
    port = port or int(api_cfg.get("port", 8000))
    app = get_app(config)
    uvicorn.run(app, host=host, port=port)


app = get_app(Config())
