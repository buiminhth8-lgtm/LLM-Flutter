"""Model export, save, and upload utilities."""

import shutil
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi, create_repo


class ModelExporter:
    """Export and upload fine-tuned models."""

    def __init__(self):
        self.api = HfApi()

    def save_model_copy(self, source_path: str, dest_path: str) -> str:
        """Copy a model to a new location."""
        src = Path(source_path)
        dst = Path(dest_path)
        dst.mkdir(parents=True, exist_ok=True)

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

        return str(dst)

    def upload_to_huggingface(
        self,
        model_path: str,
        repo_id: str,
        private: bool = True,
        token: Optional[str] = None,
        commit_message: str = "Upload fine-tuned model",
    ) -> str:
        """
        Upload a model to HuggingFace Hub.

        Args:
            model_path: Local path to the model directory.
            repo_id: Target repo id (e.g., 'username/my-model').
            private: Whether the repo should be private.
            token: HuggingFace API token (uses cached login if None).
            commit_message: Commit message for the upload.

        Returns:
            URL of the uploaded model.
        """
        # Create repo if it doesn't exist
        create_repo(repo_id, private=private, token=token, exist_ok=True)

        # Upload all files
        self.api.upload_folder(
            folder_path=model_path,
            repo_id=repo_id,
            token=token,
            commit_message=commit_message,
        )

        return f"https://huggingface.co/{repo_id}"

    def export_to_gguf(
        self,
        model_path: str,
        output_path: str,
        quantization: str = "q4_k_m",
    ) -> str:
        """
        Convert a model to GGUF format using llama.cpp's convert script.
        Requires llama.cpp to be installed.

        Args:
            model_path: Path to the HuggingFace format model.
            output_path: Output GGUF file path.
            quantization: Quantization method (q4_k_m, q5_k_m, q8_0, f16, etc.)

        Returns:
            Path to the output GGUF file.
        """
        import subprocess
        import sys

        # Try using the llama-cpp-python conversion utilities
        convert_cmd = [
            sys.executable, "-m", "llama_cpp.convert",
            "--outfile", output_path,
            "--outtype", quantization,
            model_path,
        ]

        try:
            result = subprocess.run(
                convert_cmd, capture_output=True, text=True, check=True
            )
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "GGUF conversion failed. Please install llama.cpp and ensure "
                "the convert script is available, or use the llama.cpp "
                "convert-hf-to-gguf.py script manually."
            )
