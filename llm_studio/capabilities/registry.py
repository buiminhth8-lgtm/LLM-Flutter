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
    CapabilityInfo("rag_query", CapabilityStatus.BACKEND_ONLY, "RAG query endpoints are available; Flutter has no dedicated RAG page yet.", False),
    CapabilityInfo("rag_import", CapabilityStatus.BACKEND_ONLY, "RAG import runs as a background job with upload safety checks.", False),
    CapabilityInfo("vision_ocr", CapabilityStatus.BACKEND_ONLY, "Vision and OCR endpoints exist and are GPU-scheduled; Flutter has no UI surface yet.", False),
    CapabilityInfo("lora_scan", CapabilityStatus.BACKEND_ONLY, "Adapter scanning is available in the backend.", False),
    CapabilityInfo("lora_load", CapabilityStatus.BACKEND_ONLY, "Dynamic adapter loading uses the model's PEFT-compatible adapter API.", False),
    CapabilityInfo("lora_activate", CapabilityStatus.BACKEND_ONLY, "Adapter activation/deactivation is available in the backend.", False),
    CapabilityInfo("lora_unload", CapabilityStatus.BACKEND_ONLY, "Loaded adapters can be removed through backend endpoints.", False),
    CapabilityInfo("lora_merge", CapabilityStatus.NOT_IMPLEMENTED, "The endpoint returns a failed job and does not modify base models.", False),
    CapabilityInfo("benchmark", CapabilityStatus.EXPERIMENTAL, "Backend benchmark jobs record TTFT and token/s for local development reference only.", False),
    CapabilityInfo("storage_cleanup", CapabilityStatus.PARTIAL, "Cleanup preview is available and only temporary categories are removable.", False),
    CapabilityInfo("diagnostics_export", CapabilityStatus.BACKEND_ONLY, "Diagnostics export is redacted and excludes model weights and document content.", False),
    CapabilityInfo("windows_packaging", CapabilityStatus.EXPERIMENTAL, "Launcher scripts exist; full installer validation is not claimed.", False),
    CapabilityInfo("flutter_windows", CapabilityStatus.AVAILABLE, "Flutter Windows desktop is the supported client.", True),
    CapabilityInfo("flutter_android", CapabilityStatus.NOT_IMPLEMENTED, "No Android build target is supported yet.", False),
    CapabilityInfo("flutter_linux", CapabilityStatus.NOT_IMPLEMENTED, "No Linux desktop build target is supported yet.", False),
    CapabilityInfo("flutter_macos", CapabilityStatus.NOT_IMPLEMENTED, "No macOS desktop build target is supported yet.", False),
    CapabilityInfo("flutter_web", CapabilityStatus.NOT_IMPLEMENTED, "The legacy web UI has been replaced by Flutter Windows desktop.", False),
)


def get_capabilities() -> tuple[CapabilityInfo, ...]:
    return _CAPABILITIES
