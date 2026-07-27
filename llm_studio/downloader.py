"""Model download manager - supports HuggingFace and GGUF models."""

import os
import shutil
from pathlib import Path
from typing import Optional, Callable

from huggingface_hub import (
    snapshot_download,
    hf_hub_download,
    HfApi,
    list_repo_files,
)

from .config import Config


class ModelDownloader:
    """Download and manage LLM models from HuggingFace Hub."""

    def __init__(self, config: Config):
        self.config = config
        self.models_dir = config.models_dir
        self.api = HfApi()

    def list_registry_models(self) -> list[dict]:
        """List all models in the local registry (config.yaml)."""
        return self.config.model_registry

    def list_local_models(self) -> list[dict]:
        """List all locally downloaded models."""
        models = []
        if not self.models_dir.exists():
            return models

        for item in self.models_dir.iterdir():
            if item.is_dir():
                # HuggingFace format model
                config_json = item / "config.json"
                if config_json.exists():
                    models.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "transformers",
                        "size": self._get_dir_size(item),
                    })
            elif item.suffix == ".gguf":
                models.append({
                    "name": item.stem,
                    "path": str(item),
                    "type": "gguf",
                    "size": item.stat().st_size,
                })
        return models

    def download_from_registry(
        self,
        model_name: str,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """Download a model from the registry by name."""
        registry = self.config.model_registry
        entry = None
        for m in registry:
            if m["name"] == model_name:
                entry = m
                break
        if entry is None:
            raise ValueError(f"Model '{model_name}' not found in registry.")

        return self.download_model(
            repo_id=entry["repo_id"],
            model_type=entry.get("type", "transformers"),
            filename=entry.get("filename"),
            progress_callback=progress_callback,
        )

    def download_model(
        self,
        repo_id: str,
        model_type: str = "transformers",
        filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """
        Download a model from HuggingFace Hub.

        Args:
            repo_id: HuggingFace repo id (e.g. 'Qwen/Qwen2.5-7B-Instruct')
            model_type: 'transformers' or 'gguf'
            filename: Specific file to download (for GGUF models)
            progress_callback: Optional callback(downloaded_bytes, total_bytes)

        Returns:
            Local path to the downloaded model.
        """
        if model_type == "gguf":
            if filename is None:
                # Try to find a Q4_K_M gguf file
                files = list_repo_files(repo_id)
                gguf_files = [f for f in files if f.endswith(".gguf")]
                q4_files = [f for f in gguf_files if "q4_k_m" in f.lower()]
                if q4_files:
                    filename = q4_files[0]
                elif gguf_files:
                    filename = gguf_files[0]
                else:
                    raise ValueError(f"No GGUF files found in {repo_id}")

            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(self.models_dir),
                local_dir_use_symlinks=False,
            )
            return local_path
        else:
            # Download full model (transformers format)
            local_dir = self.models_dir / repo_id.replace("/", "--")
            local_path = snapshot_download(
                repo_id=repo_id,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
            )
            return local_path

    def search_models(self, query: str, limit: int = 20) -> list[dict]:
        """Search HuggingFace Hub for models."""
        results = self.api.list_models(
            search=query,
            sort="downloads",
            direction=-1,
            limit=limit,
        )
        models = []
        for model in results:
            models.append({
                "repo_id": model.id,
                "downloads": model.downloads,
                "likes": model.likes,
                "pipeline_tag": getattr(model, "pipeline_tag", "N/A"),
            })
        return models

    def delete_model(self, model_path: str) -> bool:
        """Delete a locally downloaded model."""
        p = Path(model_path)
        if p.is_dir():
            shutil.rmtree(p)
            return True
        elif p.is_file():
            p.unlink()
            return True
        return False

    @staticmethod
    def _get_dir_size(path: Path) -> int:
        total = 0
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total
