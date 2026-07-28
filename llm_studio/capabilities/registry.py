"""Truthful feature capability registry."""

from __future__ import annotations

from dataclasses import dataclass

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
    CapabilityInfo("model_download", CapabilityStatus.BACKEND_ONLY, "Download jobs run in the backend and register successful models; Flutter only shows job status.", False),
    CapabilityInfo("model_download_cancel", CapabilityStatus.PARTIAL, "Cancellation is cooperative; snapshot_download may finish the current transfer step before stopping.", True),
    CapabilityInfo("model_download_resume", CapabilityStatus.PARTIAL, "Retry reuses the Hugging Face cache, but strict pause/resume is not exposed.", False),
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
)


def get_capabilities() -> tuple[CapabilityInfo, ...]:
    return _CAPABILITIES
