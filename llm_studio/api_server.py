"""FastAPI-based REST API server for LLM Studio.

Provides OpenAI-compatible API endpoints for third-party integration.
"""

import asyncio
import os
import secrets
import time
import uuid
import json
import base64
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from .config import Config
from .runner import create_runner, BaseRunner
from .downloader import ModelDownloader
from .rag import RAGPipeline
from .vision import VisionRunner
from .admin import AdminManager


# Loaded model runners keyed by model_path
_runners: dict[str, BaseRunner] = {}
_vision_runners: dict[str, VisionRunner] = {}
_rag_pipeline: Optional[RAGPipeline] = None
_config: Optional[Config] = None
_admin: Optional[AdminManager] = None
_model_load_lock: Optional[asyncio.Lock] = None
_inference_semaphore: Optional[asyncio.Semaphore] = None


def get_app(config: Config):
    """Create and return the FastAPI application."""
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from pydantic import BaseModel, Field

    global _config, _rag_pipeline, _admin, _model_load_lock, _inference_semaphore
    _config = config
    _admin = AdminManager(config.models_dir.parent / "data")
    _model_load_lock = asyncio.Lock()
    runtime_cfg = config.runtime
    _inference_semaphore = asyncio.Semaphore(int(runtime_cfg.get("inference_concurrency", 1)))

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

    app = FastAPI(
        title="LLM Studio API",
        description="OpenAI-compatible API for local LLM inference, RAG, and vision.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("api", {}).get(
            "cors_origins", ["http://127.0.0.1:7860", "http://localhost:7860"]
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Authentication Middleware ───────────────────────────

    auth_config = config.get("auth", {})
    auth_enabled = auth_config.get("enabled", False)

    # Paths that skip authentication
    _public_paths = {"/health", "/docs", "/openapi.json", "/redoc"}
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
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "message": "Invalid or missing authentication. Provide X-User-ID and X-API-Key headers.",
                            "type": "authentication_error",
                            "code": "invalid_api_key",
                        }
                    },
                )

            # Attach user info to request state
            request.state.user = user.to_dict()
            return await call_next(request)

    app.add_middleware(AuthMiddleware)

    # ── Pydantic Models ────────────────────────────────────

    class ChatMessage(BaseModel):
        role: str = "user"
        content: str

    class ChatRequest(BaseModel):
        model: str = Field(default="auto", description="模型路径，'auto' 自动选择")
        messages: list[ChatMessage]
        temperature: float = 0.7
        max_tokens: int = 2048
        top_p: float = 0.9
        stream: bool = False

    class ChatChoice(BaseModel):
        index: int = 0
        message: ChatMessage
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

    class ModelInfo(BaseModel):
        id: str
        object: str = "model"
        owned_by: str = "local"

    class ModelListResponse(BaseModel):
        object: str = "list"
        data: list[ModelInfo]

    class RAGIngestRequest(BaseModel):
        file_path: Optional[str] = None
        directory_path: Optional[str] = None
        recursive: bool = True

    class RAGQueryRequest(BaseModel):
        question: str
        top_k: int = 5
        model: Optional[str] = None
        temperature: float = 0.7
        max_tokens: int = 2048

    class VisionRequest(BaseModel):
        model: str = Field(..., description="视觉模型路径")
        image_path: str = Field(..., description="图片文件路径")
        prompt: str = "请详细描述这张图片的内容。"
        max_tokens: int = 1024
        temperature: float = 0.7

    class LoadModelRequest(BaseModel):
        model: str = Field(..., description="模型路径")
        model_type: str = "text"  # "text" or "vision"

    # ── Helper Functions ───────────────────────────────────

    async def _get_or_load_runner(model_path: str) -> BaseRunner:
        """Get runner, auto-loading the model if not yet loaded."""
        # Support 'auto': pick first loaded model, or first local model
        if model_path == "auto" or not model_path:
            if _runners:
                model_path = next(iter(_runners))
            else:
                try:
                    dl = ModelDownloader(config)
                    local = dl.list_local_models()
                    if local:
                        model_path = local[0]["path"]
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="No models available. Download a model first.",
                        )
                except HTTPException:
                    raise
                except Exception:
                    raise HTTPException(
                        status_code=400, detail="No models available."
                    )

        if model_path not in _runners:
            # Auto-load: compatible with LM Studio behavior
            try:
                assert _model_load_lock is not None
                async with _model_load_lock:
                    if model_path in _runners:
                        return _runners[model_path]
                    runner = create_runner(model_path, config)
                    await asyncio.to_thread(runner.load)
                    _runners[model_path] = runner
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load model '{model_path}': {e}",
                )
        return _runners[model_path]

    def _get_vision_runner(model_path: str) -> VisionRunner:
        if model_path not in _vision_runners:
            raise HTTPException(
                status_code=400,
                detail=f"Vision model not loaded: {model_path}. Call POST /v1/models/load first.",
            )
        return _vision_runners[model_path]

    # ── Endpoints: Models ──────────────────────────────────

    @app.get("/v1/models", response_model=ModelListResponse)
    async def list_models():
        """列出所有可用模型（已加载 + 已下载未加载）"""
        models = []
        seen = set()

        # 1) Already loaded models (marked as ready)
        for path in _runners:
            models.append(ModelInfo(id=path, owned_by="local:loaded"))
            seen.add(path)
        for path in _vision_runners:
            models.append(ModelInfo(id=path, owned_by="local:vision:loaded"))
            seen.add(path)

        # 2) Downloaded but not yet loaded models
        try:
            dl = ModelDownloader(config)
            for m in dl.list_local_models():
                if m["path"] not in seen:
                    models.append(ModelInfo(id=m["path"], owned_by="local:available"))
        except Exception:
            pass

        return ModelListResponse(data=models)

    @app.post("/v1/models/load")
    async def load_model(req: LoadModelRequest):
        """加载模型到内存"""
        if req.model_type == "vision":
            if req.model not in _vision_runners:
                vr = VisionRunner(req.model, config)
                vr.load()
                _vision_runners[req.model] = vr
            return {"status": "ok", "model": req.model, "type": "vision"}
        else:
            if req.model not in _runners:
                assert _model_load_lock is not None
                async with _model_load_lock:
                    if req.model not in _runners:
                        runner = create_runner(req.model, config)
                        await asyncio.to_thread(runner.load)
                        _runners[req.model] = runner
            return {"status": "ok", "model": req.model, "type": "text"}

    @app.post("/v1/models/unload")
    async def unload_model(req: LoadModelRequest):
        """卸载模型释放内存"""
        if req.model_type == "vision" and req.model in _vision_runners:
            _vision_runners[req.model].unload()
            del _vision_runners[req.model]
        elif req.model in _runners:
            _runners[req.model].unload()
            del _runners[req.model]
        return {"status": "ok", "model": req.model}

    # ── Endpoints: Chat (OpenAI-compatible) ────────────────

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatRequest):
        """OpenAI 兼容的聊天补全接口（支持 stream 模式）"""
        runner = await _get_or_load_runner(req.model)
        messages = [
            msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
            for msg in req.messages
        ]

        if not any(msg["role"] == "user" for msg in messages):
            raise HTTPException(status_code=400, detail="No user message found")

        # ── Streaming mode (SSE) ──
        if req.stream:
            from fastapi.responses import StreamingResponse

            async def event_stream():
                chat_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                created = int(time.time())
                try:
                    assert _inference_semaphore is not None
                    async with _inference_semaphore:
                        for chunk_text in runner.generate_stream(
                            messages,
                            temperature=req.temperature,
                            max_tokens=req.max_tokens,
                            top_p=req.top_p,
                        ):
                            chunk = {
                                "id": chat_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": req.model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": chunk_text},
                                    "finish_reason": None,
                                }],
                            }
                            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0)
                except Exception as e:
                    error_chunk = {"error": {"message": str(e)}}
                    yield f"data: {json.dumps(error_chunk)}\n\n"

                # Final chunk with finish_reason
                done_chunk = {
                    "id": chat_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": req.model,
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

        # ── Non-streaming mode ──
        try:
            assert _inference_semaphore is not None
            async with _inference_semaphore:
                response_text = await asyncio.to_thread(
                    runner.generate,
                    messages,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                    top_p=req.top_p,
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=req.model,
            choices=[
                ChatChoice(
                    message=ChatMessage(role="assistant", content=response_text)
                )
            ],
            usage=Usage(),
        )

    # ── Endpoints: RAG ─────────────────────────────────────

    @app.post("/v1/rag/ingest")
    async def rag_ingest(req: RAGIngestRequest):
        """投喂文档到知识库"""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        total_chunks = 0
        if req.file_path:
            total_chunks += _rag_pipeline.ingest_file(req.file_path)
        if req.directory_path:
            total_chunks += _rag_pipeline.ingest_directory(
                req.directory_path, recursive=req.recursive
            )

        _rag_pipeline.save()

        return {
            "status": "ok",
            "chunks_added": total_chunks,
            "total_chunks": _rag_pipeline.document_count,
        }

    @app.post("/v1/rag/ingest/upload")
    async def rag_ingest_upload(file: UploadFile = File(...)):
        """上传文件到知识库"""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        # Save uploaded file
        upload_dir = config.datasets_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        chunks = _rag_pipeline.ingest_file(str(file_path))
        _rag_pipeline.save()

        return {
            "status": "ok",
            "filename": file.filename,
            "chunks_added": chunks,
            "total_chunks": _rag_pipeline.document_count,
        }

    @app.post("/v1/rag/query")
    async def rag_query(req: RAGQueryRequest):
        """RAG 检索增强查询"""
        if _rag_pipeline is None:
            raise HTTPException(status_code=500, detail="RAG pipeline not initialized")

        # Retrieve relevant docs
        results = _rag_pipeline.query(req.question, top_k=req.top_k)

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
        if req.model and req.model in _runners:
            runner = _runners[req.model]
            rag_prompt = _rag_pipeline.build_rag_prompt(req.question, top_k=req.top_k)
            answer = runner.generate(
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
        """查看知识库状态"""
        if _rag_pipeline is None:
            return {"status": "not_initialized"}
        return {
            "status": "ok",
            "document_count": _rag_pipeline.document_count,
            "sources": _rag_pipeline.get_ingested_sources(),
        }

    @app.post("/v1/rag/clear")
    async def rag_clear():
        """清空知识库"""
        if _rag_pipeline:
            _rag_pipeline.clear()
        return {"status": "ok"}

    # ── Endpoints: Vision ──────────────────────────────────

    @app.post("/v1/vision/analyze")
    async def vision_analyze(req: VisionRequest):
        """图片识别分析"""
        vr = _get_vision_runner(req.model)
        try:
            response = vr.analyze_image(
                req.image_path,
                prompt=req.prompt,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            )
            return {
                "image": req.image_path,
                "prompt": req.prompt,
                "response": response,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/vision/analyze/upload")
    async def vision_analyze_upload(
        model: str = Form(...),
        prompt: str = Form("请详细描述这张图片的内容。"),
        max_tokens: int = Form(1024),
        file: UploadFile = File(...),
    ):
        """上传图片进行识别"""
        vr = _get_vision_runner(model)

        # Save uploaded image
        upload_dir = config.datasets_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        try:
            response = vr.analyze_image(
                str(file_path), prompt=prompt, max_tokens=max_tokens
            )
            return {
                "filename": file.filename,
                "prompt": prompt,
                "response": response,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/vision/ocr")
    async def vision_ocr(
        model: str = Form(...),
        file: UploadFile = File(...),
    ):
        """图片 OCR 文字识别"""
        vr = _get_vision_runner(model)

        upload_dir = config.datasets_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        try:
            text = vr.ocr_image(str(file_path))
            return {"filename": file.filename, "text": text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── Health Check ───────────────────────────────────────

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "loaded_text_models": list(_runners.keys()),
            "loaded_vision_models": list(_vision_runners.keys()),
            "rag_documents": _rag_pipeline.document_count if _rag_pipeline else 0,
        }

    # ── Admin Backend ──────────────────────────────────────

    from fastapi.responses import HTMLResponse

    # Simple session token store (in-memory, cleared on restart)
    _admin_sessions: set[str] = set()

    class AdminLoginRequest(BaseModel):
        password: str

    class AdminCreateUserRequest(BaseModel):
        user_id: str
        role: str = "user"
        note: str = ""

    class AdminUpdateUserRequest(BaseModel):
        role: Optional[str] = None
        note: Optional[str] = None

    class AdminChangePasswordRequest(BaseModel):
        old_password: str
        new_password: str

    def _verify_admin_session(request: Request):
        """Verify admin session token from cookie."""
        token = request.cookies.get("admin_token", "")
        if token not in _admin_sessions:
            raise HTTPException(status_code=401, detail="请先登录管理后台")

    @app.post("/admin/api/login")
    async def admin_login(request: Request, req: AdminLoginRequest):
        """管理后台登录"""
        if not _admin.verify_admin_password(req.password):
            raise HTTPException(status_code=401, detail="密码错误")
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
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.delete("/admin/api/users/{user_id}")
    async def admin_delete_user(request: Request, user_id: str):
        _verify_admin_session(request)
        if not _admin.delete_user(user_id):
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"status": "ok"}

    @app.put("/admin/api/users/{user_id}")
    async def admin_update_user(request: Request, user_id: str, req: AdminUpdateUserRequest):
        _verify_admin_session(request)
        if not _admin.update_user(user_id, role=req.role, note=req.note):
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"status": "ok"}

    @app.post("/admin/api/users/{user_id}/toggle")
    async def admin_toggle_user(request: Request, user_id: str):
        _verify_admin_session(request)
        result = _admin.toggle_user(user_id)
        if result is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"status": "ok", "enabled": result}

    @app.post("/admin/api/users/{user_id}/regenerate")
    async def admin_regenerate_key(request: Request, user_id: str):
        _verify_admin_session(request)
        new_key = _admin.regenerate_key(user_id)
        if not new_key:
            raise HTTPException(status_code=404, detail="用户不存在")
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
            raise HTTPException(status_code=400, detail="原密码错误")
        return {"status": "ok"}

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page():
        """管理后台页面"""
        html_path = Path(__file__).parent / "admin_ui.html"
        if html_path.exists():
            return HTMLResponse(html_path.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>Admin UI not found</h1>", status_code=500)

    # ── /api/v1 alias (RemoteAssistant compatibility) ──────
    # RemoteAssistant llmstudio preset uses /api/v1/* paths
    from fastapi import APIRouter
    from starlette.routing import Mount

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
    async def api_v1_chat(req: ChatRequest):
        return await chat_completions(req)

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
