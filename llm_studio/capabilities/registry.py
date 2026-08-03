"""Truthful feature capability registry."""

from __future__ import annotations

from dataclasses import dataclass, replace

from llm_studio.features import (
    is_adapter_evaluation_enabled,
    is_dataset_builder_enabled,
    is_dataset_versioning_enabled,
    is_evaluation_center_enabled,
    is_finetune_center_enabled,
    is_memory_retrieval_enabled,
    is_novel_memory_enabled,
    is_novel_studio_enabled,
    is_revision_system_enabled,
    is_training_recipe_recommender_enabled,
)

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
    CapabilityInfo("version_api", CapabilityStatus.AVAILABLE, "Version metadata is available through /v1/version and diagnostics.", True),
    CapabilityInfo("health_checks", CapabilityStatus.AVAILABLE, "Quick and full local health checks are available through /v1/health.", True),
    CapabilityInfo("diagnostics_export", CapabilityStatus.AVAILABLE, "Diagnostics export is exposed in Flutter and excludes model weights, document content, and secrets.", True),
    CapabilityInfo("backup_restore", CapabilityStatus.AVAILABLE, "Local data backup and restore scripts are available without packaging model weights.", False),
    CapabilityInfo("windows_packaging", CapabilityStatus.AVAILABLE, "Windows launch, environment check, diagnostics, backup, restore, and packaging scripts are available.", False),
    CapabilityInfo("windows_desktop_release", CapabilityStatus.AVAILABLE, "Flutter Windows desktop release packaging is documented and scripted for local validation.", True),
    CapabilityInfo("flutter_windows", CapabilityStatus.AVAILABLE, "Flutter Windows desktop is the supported client.", True),
    CapabilityInfo("flutter_android", CapabilityStatus.NOT_IMPLEMENTED, "No Android build target is supported yet.", False),
    CapabilityInfo("flutter_linux", CapabilityStatus.NOT_IMPLEMENTED, "No Linux desktop build target is supported yet.", False),
    CapabilityInfo("flutter_macos", CapabilityStatus.NOT_IMPLEMENTED, "No macOS desktop build target is supported yet.", False),
    CapabilityInfo("flutter_web", CapabilityStatus.NOT_IMPLEMENTED, "The legacy web UI has been replaced by Flutter Windows desktop.", False),
    CapabilityInfo("novel_studio", CapabilityStatus.NOT_IMPLEMENTED, "Novel Studio is a staged roadmap item; Stage 0 only prepares feature flags, documentation, and placeholders.", False),
    CapabilityInfo("novel_studio_product_ui", CapabilityStatus.NOT_IMPLEMENTED, "Novel Studio productized dashboard and journey navigation require novel_studio to be enabled.", False),
    CapabilityInfo("novel_projects", CapabilityStatus.NOT_IMPLEMENTED, "Novel project CRUD is not implemented in Stage 0.", False),
    CapabilityInfo("prompt_studio", CapabilityStatus.NOT_IMPLEMENTED, "Prompt Studio templates are planned for a later stage.", False),
    CapabilityInfo("context_assembler", CapabilityStatus.NOT_IMPLEMENTED, "Context Assembler is disabled until Novel Studio is enabled.", False),
    CapabilityInfo("context_budget", CapabilityStatus.NOT_IMPLEMENTED, "Novel context budget management is disabled.", False),
    CapabilityInfo("context_render_preview", CapabilityStatus.NOT_IMPLEMENTED, "Context-based Prompt preview is disabled.", False),
    CapabilityInfo("writing_workspace", CapabilityStatus.NOT_IMPLEMENTED, "The novel writing workspace is planned but not implemented.", False),
    CapabilityInfo("writing_stream", CapabilityStatus.NOT_IMPLEMENTED, "Novel writing streaming is disabled until Stage 4 is enabled.", False),
    CapabilityInfo("writing_save_to_chapter", CapabilityStatus.NOT_IMPLEMENTED, "Saving generated text to chapter drafts is disabled until Stage 4 is enabled.", False),
    CapabilityInfo("revision_system", CapabilityStatus.NOT_IMPLEMENTED, "Revision and version workflows are planned but not implemented.", False),
    CapabilityInfo("revision_diff", CapabilityStatus.NOT_IMPLEMENTED, "Revision diff persistence is planned but not implemented.", False),
    CapabilityInfo("revision_autosave", CapabilityStatus.NOT_IMPLEMENTED, "Revision autosaves are planned but not implemented.", False),
    CapabilityInfo("dataset_builder", CapabilityStatus.NOT_IMPLEMENTED, "Novel dataset building is planned but not implemented.", False),
    CapabilityInfo("dataset_sft_export", CapabilityStatus.NOT_IMPLEMENTED, "Draft SFT JSONL export is planned for Dataset Builder.", False),
    CapabilityInfo("dataset_preference_samples", CapabilityStatus.NOT_IMPLEMENTED, "Preference sample structure is planned for Dataset Builder.", False),
    CapabilityInfo("dataset_versioning", CapabilityStatus.NOT_IMPLEMENTED, "Immutable DatasetVersion is planned for a later stage.", False),
    CapabilityInfo("dataset_freeze", CapabilityStatus.NOT_IMPLEMENTED, "Dataset freeze is planned for DatasetVersion.", False),
    CapabilityInfo("dataset_manifest", CapabilityStatus.NOT_IMPLEMENTED, "Dataset manifests are planned for DatasetVersion.", False),
    CapabilityInfo("dataset_train_val_split", CapabilityStatus.NOT_IMPLEMENTED, "Dataset train/validation split is planned for DatasetVersion.", False),
    CapabilityInfo("training_recipe_recommender", CapabilityStatus.NOT_IMPLEMENTED, "Training recipe recommendation is planned for a later stage.", False),
    CapabilityInfo("finetune_center", CapabilityStatus.NOT_IMPLEMENTED, "Novel-specific fine-tune workflows are not implemented.", False),
    CapabilityInfo("finetune_preflight", CapabilityStatus.NOT_IMPLEMENTED, "Fine-tune preflight checks are not implemented.", False),
    CapabilityInfo("finetune_runs", CapabilityStatus.NOT_IMPLEMENTED, "FineTuneRun execution is not implemented.", False),
    CapabilityInfo("finetune_metrics", CapabilityStatus.NOT_IMPLEMENTED, "Fine-tune metrics are not implemented.", False),
    CapabilityInfo("finetune_checkpoints", CapabilityStatus.NOT_IMPLEMENTED, "Fine-tune checkpoint tracking is not implemented.", False),
    CapabilityInfo("adapter_training", CapabilityStatus.NOT_IMPLEMENTED, "Adapter training and registration are not implemented.", False),
    CapabilityInfo("adapter_registration_after_training", CapabilityStatus.NOT_IMPLEMENTED, "Adapter registration after training is not implemented.", False),
    CapabilityInfo("adapter_evaluation", CapabilityStatus.NOT_IMPLEMENTED, "Adapter quality evaluation is not implemented.", False),
    CapabilityInfo("adapter_base_compare", CapabilityStatus.NOT_IMPLEMENTED, "Base-vs-adapter comparison is not implemented.", False),
    CapabilityInfo("adapter_manual_scoring", CapabilityStatus.NOT_IMPLEMENTED, "Manual adapter comparison scoring is not implemented.", False),
    CapabilityInfo("adapter_evaluation_report", CapabilityStatus.NOT_IMPLEMENTED, "Adapter evaluation reports are not implemented.", False),
    CapabilityInfo("full_evaluation_center", CapabilityStatus.NOT_IMPLEMENTED, "Full automatic Evaluation Center is not implemented.", False),
    CapabilityInfo("evaluation_repetition", CapabilityStatus.NOT_IMPLEMENTED, "Repetition evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_style_consistency", CapabilityStatus.NOT_IMPLEMENTED, "Style consistency evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_character_consistency", CapabilityStatus.NOT_IMPLEMENTED, "Character consistency evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_world_consistency", CapabilityStatus.NOT_IMPLEMENTED, "World consistency evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_plot_coherence", CapabilityStatus.NOT_IMPLEMENTED, "Plot coherence evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_pacing", CapabilityStatus.NOT_IMPLEMENTED, "Pacing evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_memory_usage", CapabilityStatus.NOT_IMPLEMENTED, "Memory usage evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_foreshadowing", CapabilityStatus.NOT_IMPLEMENTED, "Foreshadowing evaluation is planned but not implemented.", False),
    CapabilityInfo("evaluation_local_model_judge", CapabilityStatus.NOT_IMPLEMENTED, "Local model assisted evaluation is planned but not implemented.", False),
    CapabilityInfo("novel_rag_memory", CapabilityStatus.NOT_IMPLEMENTED, "Novel memory and long-form RAG are planned but not implemented.", False),
    CapabilityInfo("memory_documents", CapabilityStatus.NOT_IMPLEMENTED, "Novel memory documents are planned but not implemented.", False),
    CapabilityInfo("memory_keyword_retrieval", CapabilityStatus.NOT_IMPLEMENTED, "Keyword memory retrieval is planned but not implemented.", False),
    CapabilityInfo("memory_sqlite_fts", CapabilityStatus.NOT_IMPLEMENTED, "SQLite FTS memory retrieval is planned but not implemented.", False),
    CapabilityInfo("memory_embedding_retrieval", CapabilityStatus.NOT_IMPLEMENTED, "Embedding memory retrieval is planned but not implemented.", False),
    CapabilityInfo("chapter_summary_versions", CapabilityStatus.NOT_IMPLEMENTED, "Chapter summary versions are planned but not implemented.", False),
    CapabilityInfo("context_memory_bridge", CapabilityStatus.NOT_IMPLEMENTED, "ContextAssembler memory bridge is planned but not implemented.", False),
    CapabilityInfo("novel_evaluation", CapabilityStatus.NOT_IMPLEMENTED, "Novel evaluation workflows are planned but not implemented.", False),
)


def get_capabilities() -> tuple[CapabilityInfo, ...]:
    return _CAPABILITIES


def get_capabilities_for_config(config) -> tuple[CapabilityInfo, ...]:
    """Return capabilities with config-driven feature flags applied."""
    if not is_novel_studio_enabled(config):
        return _CAPABILITIES
    overrides = {
        "novel_studio": (CapabilityStatus.PARTIAL, "Novel Studio foundations through Stage 12 productized UI are available.", True),
        "novel_studio_product_ui": (CapabilityStatus.AVAILABLE, "Novel Studio Dashboard, unified navigation, capability gates, and release-oriented UX states are available.", True),
        "novel_projects": (CapabilityStatus.AVAILABLE, "Novel project CRUD is available.", True),
        "novel_world_bible": (CapabilityStatus.AVAILABLE, "Novel world bible entries are available.", True),
        "novel_characters": (CapabilityStatus.AVAILABLE, "Novel character records are available.", True),
        "novel_chapters": (CapabilityStatus.AVAILABLE, "Novel volumes, chapters, scenes, plot threads, and timeline records are available.", True),
        "prompt_studio": (CapabilityStatus.AVAILABLE, "Prompt templates, immutable versions, and preview rendering are available.", True),
        "prompt_template_versions": (CapabilityStatus.AVAILABLE, "Prompt template version history and activation are available.", True),
        "prompt_render_preview": (CapabilityStatus.AVAILABLE, "Prompt rendering preview is available without calling Runtime or Runner.", True),
        "context_assembler": (CapabilityStatus.AVAILABLE, "Novel records are selected, prioritized, budgeted, and assembled without calling Runtime.", True),
        "context_budget": (CapabilityStatus.AVAILABLE, "Deterministic token and character budgets with priority-based truncation are available.", True),
        "context_render_preview": (CapabilityStatus.AVAILABLE, "Assembled variables can be rendered through PromptRenderer without model generation.", True),
        "writing_workspace": (CapabilityStatus.AVAILABLE, "Local novel writing reuses ContextAssembler, PromptRenderer, and the existing Runtime.", True),
        "writing_stream": (CapabilityStatus.AVAILABLE, "Writing generation supports persisted SSE streaming and cooperative cancellation.", True),
        "writing_save_to_chapter": (CapabilityStatus.AVAILABLE, "Successful generations can be saved to draft_content or summary; final_content is protected.", True),
    }
    if is_revision_system_enabled(config):
        overrides.update(
            {
                "revision_system": (CapabilityStatus.AVAILABLE, "Human revision records can be created from generation history, chapter drafts, or manual text.", True),
                "revision_diff": (CapabilityStatus.AVAILABLE, "Backend-generated diff_json is persisted for every formal revision save.", True),
                "revision_autosave": (CapabilityStatus.AVAILABLE, "Revision editor autosaves are stored separately from formal revision records.", True),
            }
        )
    if is_dataset_builder_enabled(config):
        overrides.update(
            {
                "dataset_builder": (CapabilityStatus.AVAILABLE, "Approved revision candidates can be transformed into reviewed training samples.", True),
                "dataset_sft_export": (CapabilityStatus.AVAILABLE, "Approved SFT samples can be exported as draft JSONL files.", True),
                "dataset_preference_samples": (CapabilityStatus.PARTIAL, "Preference sample fields and draft creation are available; DPO training is not implemented.", True),
            }
        )
    if is_dataset_versioning_enabled(config):
        overrides.update(
            {
                "dataset_versioning": (CapabilityStatus.AVAILABLE, "Approved samples can be frozen into immutable DatasetVersion records.", True),
                "dataset_freeze": (CapabilityStatus.AVAILABLE, "Ready or dirty datasets can be frozen into train/val JSONL artifacts.", True),
                "dataset_manifest": (CapabilityStatus.AVAILABLE, "DatasetVersion manifest.json records split, counts, hashes, and warnings.", True),
                "dataset_train_val_split": (CapabilityStatus.AVAILABLE, "Dataset freeze supports grouped train/validation split without continuous token slicing.", True),
            }
        )
    elif is_dataset_builder_enabled(config):
        overrides["dataset_versioning"] = (
            CapabilityStatus.NOT_IMPLEMENTED,
            "DatasetVersion is disabled by feature flag.",
            False,
        )
    if is_training_recipe_recommender_enabled(config):
        overrides["training_recipe_recommender"] = (
            CapabilityStatus.AVAILABLE,
            "Draft LoRA/QLoRA recipe recommendation is available without launching training.",
            True,
        )
    if is_finetune_center_enabled(config):
        overrides.update(
            {
                "finetune_center": (CapabilityStatus.AVAILABLE, "Fine-tune Center can create queued LoRA/QLoRA runs from frozen DatasetVersions and confirmed recipes.", True),
                "finetune_preflight": (CapabilityStatus.AVAILABLE, "Preflight validates dataset artifacts, recipes, base model, dependencies, GPU, and output paths before queueing.", True),
                "finetune_runs": (CapabilityStatus.AVAILABLE, "FineTuneRun lifecycle is persisted and executed through JobQueue.", True),
                "finetune_metrics": (CapabilityStatus.AVAILABLE, "Fine-tune train/eval metrics and sanitized logs are available for Flutter.", True),
                "finetune_checkpoints": (CapabilityStatus.AVAILABLE, "Best and last checkpoints are tracked separately for resume.", True),
                "adapter_training": (CapabilityStatus.PARTIAL, "LoRA/QLoRA training has a real trainer interface; fake trainer is test-only and real runs require local dependencies and GPU.", True),
                "adapter_registration_after_training": (CapabilityStatus.AVAILABLE, "Completed runs register produced adapters without auto activation.", True),
            }
        )
    if is_adapter_evaluation_enabled(config):
        overrides.update(
            {
                "adapter_evaluation": (CapabilityStatus.AVAILABLE, "Adapter Evaluation sessions compare base model and base+adapter outputs under frozen prompt/context/params.", True),
                "adapter_base_compare": (CapabilityStatus.AVAILABLE, "Base-vs-adapter side-by-side generation uses WritingRuntimeBridge with identical prompt and params.", True),
                "adapter_manual_scoring": (CapabilityStatus.AVAILABLE, "Human reviewers can score base and adapter results and choose a winner.", True),
                "adapter_evaluation_report": (CapabilityStatus.AVAILABLE, "Lightweight reports summarize manual scores and win counts.", True),
                "full_evaluation_center": (CapabilityStatus.NOT_IMPLEMENTED, "Full automatic Evaluation Center is intentionally out of Stage 9 scope.", False),
            }
        )
    if is_novel_memory_enabled(config):
        overrides.update(
            {
                "novel_rag_memory": (CapabilityStatus.AVAILABLE, "Novel Memory / RAG documents, chunks, retrieval traces, and ContextAssembler bridge are available.", True),
                "memory_documents": (CapabilityStatus.AVAILABLE, "Memory documents can be created manually or built from existing novel data.", True),
                "memory_keyword_retrieval": (CapabilityStatus.AVAILABLE, "Deterministic keyword retrieval is available without external vector services.", True),
                "memory_sqlite_fts": (CapabilityStatus.PARTIAL, "SQLite FTS5 is used when available and falls back to keyword retrieval when unavailable.", True),
                "memory_embedding_retrieval": (CapabilityStatus.NOT_IMPLEMENTED, "Embedding retrieval remains a reserved interface in Stage 10.", False),
                "chapter_summary_versions": (CapabilityStatus.AVAILABLE, "Manual and model-generated chapter summary versions are persisted.", True),
                "context_memory_bridge": (CapabilityStatus.AVAILABLE, "ContextAssembler can inject budgeted retrieved_memory when memory.enabled=true.", True),
                "full_evaluation_center": (CapabilityStatus.NOT_IMPLEMENTED, "Full automatic Evaluation Center is intentionally out of Stage 10 scope.", False),
                "novel_evaluation": (CapabilityStatus.NOT_IMPLEMENTED, "Automatic literary evaluation remains out of scope.", False),
            }
        )
        if not is_memory_retrieval_enabled(config):
            overrides["memory_keyword_retrieval"] = (
                CapabilityStatus.NOT_IMPLEMENTED,
                "Memory retrieval is disabled by feature flag.",
                False,
            )
    if is_evaluation_center_enabled(config):
        overrides.update(
            {
                "full_evaluation_center": (CapabilityStatus.AVAILABLE, "Full Evaluation Center runs deterministic heuristic evaluators and optional local model judging.", True),
                "novel_evaluation": (CapabilityStatus.AVAILABLE, "Novel quality evaluation runs are persisted with metrics, findings, reports, and manual scores.", True),
                "evaluation_repetition": (CapabilityStatus.AVAILABLE, "Sentence, paragraph, and phrase repetition heuristics are available.", True),
                "evaluation_style_consistency": (CapabilityStatus.AVAILABLE, "Style heuristic metrics compare sentence length, punctuation, dialogue ratio, and POV signals.", True),
                "evaluation_character_consistency": (CapabilityStatus.AVAILABLE, "Character consistency heuristics compare text against known character records.", True),
                "evaluation_world_consistency": (CapabilityStatus.AVAILABLE, "World consistency heuristics compare text against world entries and timeline records.", True),
                "evaluation_plot_coherence": (CapabilityStatus.AVAILABLE, "Plot coherence heuristics compare chapter goals, outlines, and open plot threads.", True),
                "evaluation_pacing": (CapabilityStatus.AVAILABLE, "Pacing heuristics measure dialogue, description, action ratio, and long paragraphs.", True),
                "evaluation_memory_usage": (CapabilityStatus.AVAILABLE, "Memory/RAG retrieval relevance and usage are evaluated from persisted retrieval records.", True),
                "evaluation_foreshadowing": (CapabilityStatus.AVAILABLE, "Foreshadowing heuristics inspect registered clues from world, plot, timeline, and memory sources.", True),
                "evaluation_local_model_judge": (CapabilityStatus.PARTIAL, "Optional local-model assisted judging reuses loaded Runtime and is advisory only.", True),
                "windows_packaging": (CapabilityStatus.AVAILABLE, "Windows launch, environment check, diagnostics, backup, restore, and packaging scripts are available.", False),
                "windows_desktop_release": (CapabilityStatus.AVAILABLE, "Windows desktop release packaging is available for local validation.", True),
            }
        )
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
