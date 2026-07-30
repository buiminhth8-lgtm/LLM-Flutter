"""Truthful feature capability registry."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llm_studio.features import is_novel_studio_enabled

from .status import CapabilityStatus


@dataclass(frozen=True)
class CapabilityInfo:
    name: str
    status: CapabilityStatus
    reason: str
    frontend_exposed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status.value,
            "reason": self.reason,
            "frontend_exposed": self.frontend_exposed,
        }


_CAPABILITIES: tuple[CapabilityInfo, ...] = (
    CapabilityInfo("chat_non_stream", CapabilityStatus.AVAILABLE, "FastAPI and Flutter use the selected loaded model.", True),
    CapabilityInfo("chat_stream", CapabilityStatus.AVAILABLE, "SSE streaming chat is available in the backend and Flutter Windows client.", True),
    CapabilityInfo("model_scan", CapabilityStatus.AVAILABLE, "Scans the unified LocalModelRepository without loading weights.", True),
    CapabilityInfo("model_load", CapabilityStatus.AVAILABLE, "Loads a selected repository model through the runtime policy and GPU scheduler.", True),
    CapabilityInfo("model_unload", CapabilityStatus.AVAILABLE, "Unloads the selected runtime model and releases CUDA cache via the backend.", True),
    CapabilityInfo("model_download", CapabilityStatus.AVAILABLE, "Download jobs run in the backend and are visible in Flutter.", True),
    CapabilityInfo("model_download_huggingface", CapabilityStatus.NOT_IMPLEMENTED, "Hugging Face remote download provider has been removed; local Transformers/HF-format models remain supported.", False),
    CapabilityInfo("model_download_modelscope", CapabilityStatus.PARTIAL, "ModelScope is the only remote download provider; byte totals may be unavailable.", True),
    CapabilityInfo("model_download_progress", CapabilityStatus.PARTIAL, "Progress uses ModelScope metadata when available; percent is null when total bytes are unknown.", True),
    CapabilityInfo("model_download_cancel", CapabilityStatus.PARTIAL, "Cancellation is cooperative; the current file transfer may finish before the job stops.", True),
    CapabilityInfo("model_download_retry", CapabilityStatus.AVAILABLE, "Failed, cancelled, and interrupted downloads can be retried with ModelScope cache reuse.", True),
    CapabilityInfo("model_download_resume", CapabilityStatus.PARTIAL, "Retry reuses the ModelScope cache, but strict pause/resume is not claimed.", True),
    CapabilityInfo("model_download_auto_register", CapabilityStatus.AVAILABLE, "Successful downloads are scanned into LocalModelRepository and write back model_id.", True),
    CapabilityInfo("rag_query", CapabilityStatus.PARTIAL, "RAG query is exposed in the Flutter Windows client as a minimum query test surface.", True),
    CapabilityInfo("rag_import", CapabilityStatus.BACKEND_ONLY, "RAG import runs as a background job with upload safety checks; the Flutter page does not expose full import controls yet.", False),
    CapabilityInfo("vision_ocr", CapabilityStatus.BACKEND_ONLY, "Vision and OCR endpoints exist and are GPU-scheduled; Flutter has no UI surface yet.", False),
    CapabilityInfo("lora_scan", CapabilityStatus.PARTIAL, "Adapter scanning is exposed in the Flutter Windows client.", True),
    CapabilityInfo("lora_load", CapabilityStatus.PARTIAL, "Dynamic adapter loading requires a selected or loaded base model and is exposed in Flutter.", True),
    CapabilityInfo("lora_activate", CapabilityStatus.PARTIAL, "Adapter activation/deactivation is exposed in Flutter and defaults to one active adapter.", True),
    CapabilityInfo("lora_unload", CapabilityStatus.PARTIAL, "Loaded adapters can be removed through backend endpoints; Flutter exposes activate/deactivate, not a full adapter inventory manager.", True),
    CapabilityInfo("lora_merge", CapabilityStatus.NOT_IMPLEMENTED, "The endpoint returns a failed job and does not modify base models.", False),
    CapabilityInfo("benchmark", CapabilityStatus.EXPERIMENTAL, "Backend benchmark jobs record TTFT and token/s for local development reference only.", False),
    CapabilityInfo("benchmark_with_adapter", CapabilityStatus.NOT_IMPLEMENTED, "Benchmark adapter_id is rejected unless a runner explicitly supports adapter loading; Flutter hides adapter selection.", False),
    CapabilityInfo("storage_cleanup", CapabilityStatus.PARTIAL, "Cleanup preview and execution are exposed in Flutter; only temporary categories are removable.", True),
    CapabilityInfo("diagnostics_export", CapabilityStatus.PARTIAL, "Diagnostics export is exposed in Flutter and excludes model weights, document content, and secrets.", True),
    CapabilityInfo("windows_packaging", CapabilityStatus.EXPERIMENTAL, "Launcher scripts exist; full installer validation is not claimed.", False),
    CapabilityInfo("flutter_windows", CapabilityStatus.AVAILABLE, "Flutter Windows desktop is the supported client.", True),
    CapabilityInfo("flutter_android", CapabilityStatus.NOT_IMPLEMENTED, "No Android build target is supported yet.", False),
    CapabilityInfo("flutter_linux", CapabilityStatus.NOT_IMPLEMENTED, "No Linux desktop build target is supported yet.", False),
    CapabilityInfo("flutter_macos", CapabilityStatus.NOT_IMPLEMENTED, "No macOS desktop build target is supported yet.", False),
    CapabilityInfo("flutter_web", CapabilityStatus.NOT_IMPLEMENTED, "The legacy web UI has been replaced by Flutter Windows desktop.", False),
    CapabilityInfo("novel_studio", CapabilityStatus.NOT_IMPLEMENTED, "Novel Studio is a staged roadmap item; Stage 0 only prepares feature flags, documentation, and placeholders.", False),
    CapabilityInfo("novel_projects", CapabilityStatus.NOT_IMPLEMENTED, "Novel project CRUD is not implemented in Stage 0.", False),
    CapabilityInfo("prompt_studio", CapabilityStatus.NOT_IMPLEMENTED, "Prompt Studio templates are planned for a later stage.", False),
    CapabilityInfo("writing_workspace", CapabilityStatus.NOT_IMPLEMENTED, "The novel writing workspace is planned but not implemented.", False),
    CapabilityInfo("revision_system", CapabilityStatus.NOT_IMPLEMENTED, "Revision and version workflows are planned but not implemented.", False),
    CapabilityInfo("dataset_builder", CapabilityStatus.NOT_IMPLEMENTED, "Novel dataset building is planned but not implemented.", False),
    CapabilityInfo("finetune_center", CapabilityStatus.PARTIAL, "Core LoRA/QLoRA plumbing exists, but Novel-specific fine-tune workflows are not implemented.", False),
    CapabilityInfo("novel_rag_memory", CapabilityStatus.NOT_IMPLEMENTED, "Novel memory and long-form RAG are planned but not implemented.", False),
    CapabilityInfo("novel_evaluation", CapabilityStatus.NOT_IMPLEMENTED, "Novel evaluation workflows are planned but not implemented.", False),
)


def get_capabilities() -> tuple[CapabilityInfo, ...]:
    return _CAPABILITIES


def get_capabilities_for_config(config) -> tuple[CapabilityInfo, ...]:
    """Return capabilities with config-driven feature flags applied."""
    if not is_novel_studio_enabled(config):
        return _CAPABILITIES
    overrides = {
        "novel_studio": (CapabilityStatus.PARTIAL, "Novel Studio Stage 2 foundation and Prompt Studio preview APIs are available.", True),
        "novel_projects": (CapabilityStatus.AVAILABLE, "Novel project CRUD is available.", True),
        "novel_world_bible": (CapabilityStatus.AVAILABLE, "Novel world bible entries are available.", True),
        "novel_characters": (CapabilityStatus.AVAILABLE, "Novel character records are available.", True),
        "novel_chapters": (CapabilityStatus.AVAILABLE, "Novel volumes, chapters, scenes, plot threads, and timeline records are available.", True),
        "prompt_studio": (CapabilityStatus.AVAILABLE, "Prompt templates, immutable versions, and preview rendering are available.", True),
        "prompt_template_versions": (CapabilityStatus.AVAILABLE, "Prompt template version history and activation are available.", True),
        "prompt_render_preview": (CapabilityStatus.AVAILABLE, "Prompt rendering preview is available without calling Runtime or Runner.", True),
        "context_assembler": (CapabilityStatus.NOT_IMPLEMENTED, "Context Assembler is planned for Stage 3 and not implemented in Stage 2.", False),
    }
    existing = {cap.name for cap in _CAPABILITIES}
    result: list[CapabilityInfo] = []
    for cap in _CAPABILITIES:
        if cap.name in overrides:
            status, reason, frontend = overrides[cap.name]
            result.append(replace(cap, status=status, reason=reason, frontend_exposed=frontend))
        else:
            result.append(cap)
    for name, (status, description, frontend) in overrides.items():
        if name not in existing:
            result.append(CapabilityInfo(name, status, description, frontend))
    return tuple(result)
