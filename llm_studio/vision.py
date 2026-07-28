"""Vision module - Image recognition and multimodal understanding."""

import base64
from pathlib import Path

from .config import Config, get_device
from .runtime.capabilities import detect_runtime_capabilities


class VisionRunner:
    """Run vision-language models for image understanding."""

    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    def __init__(self, model_path: str, config: Config):
        self.model_path = model_path
        self.config = config
        self.model = None
        self.processor = None

    def load(self):
        """Load a vision-language model (Qwen2-VL, LLaVA, etc.)."""
        import torch
        from transformers import AutoModelForVision2Seq, AutoProcessor

        caps = detect_runtime_capabilities(run_bnb_probe=False)
        device = get_device()
        dtype = torch.bfloat16 if device != "cpu" and caps.bf16_supported else torch.float16 if device != "cpu" else torch.float32
        trust_remote_code = bool(self.config.runtime.get("trust_remote_code", False))

        self.processor = AutoProcessor.from_pretrained(
            self.model_path, trust_remote_code=trust_remote_code
        )

        load_kwargs = {
            "pretrained_model_name_or_path": self.model_path,
            "torch_dtype": dtype,
            "device_map": "auto" if device != "cpu" else None,
            "trust_remote_code": trust_remote_code,
        }

        # Try Vision2Seq first, fall back to generic auto model
        try:
            self.model = AutoModelForVision2Seq.from_pretrained(**load_kwargs)
        except Exception:
            from transformers import AutoModel
            self.model = AutoModel.from_pretrained(**load_kwargs)

        self.model.eval()

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "请详细描述这张图片的内容。",
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Analyze an image with a text prompt.

        Args:
            image_path: Path to the image file.
            prompt: Question or instruction about the image.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Model's text response about the image.
        """
        import torch
        from PIL import Image

        img = Image.open(image_path).convert("RGB")

        # Build messages in chat format for vision models
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Try chat template approach (Qwen2-VL style)
        try:
            text_input = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.processor(
                text=[text_input], images=[img], return_tensors="pt", padding=True
            )
        except Exception:
            # Fallback: direct processor call (LLaVA style)
            inputs = self.processor(
                text=prompt, images=img, return_tensors="pt", padding=True
            )

        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
            )

        # Decode only new tokens
        input_len = inputs.get("input_ids", torch.tensor([[]])).shape[-1]
        new_tokens = outputs[0][input_len:]
        response = self.processor.decode(new_tokens, skip_special_tokens=True)
        return response

    def analyze_image_batch(
        self,
        image_paths: list[str],
        prompt: str = "请详细描述这张图片的内容。",
        max_tokens: int = 1024,
    ) -> list[dict]:
        """Analyze multiple images."""
        results = []
        for path in image_paths:
            try:
                response = self.analyze_image(path, prompt, max_tokens)
                results.append({
                    "image": path,
                    "response": response,
                    "status": "success",
                })
            except Exception as e:
                results.append({
                    "image": path,
                    "response": str(e),
                    "status": "error",
                })
        return results

    def ocr_image(self, image_path: str) -> str:
        """Extract text from an image (OCR). Uses vision model or dedicated OCR."""
        vision_cfg = self.config.get("vision", {})
        backend = vision_cfg.get("ocr_backend", "auto")
        if backend in {"paddle", "paddleocr"}:
            return self._ocr_with_paddleocr(image_path)
        if backend == "easyocr":
            return self._ocr_with_easyocr(image_path, gpu=bool(vision_cfg.get("ocr_gpu", False)))
        if backend == "auto":
            for _name, func in (
                ("easyocr", lambda: self._ocr_with_easyocr(image_path, gpu=False)),
                ("paddleocr", lambda: self._ocr_with_paddleocr(image_path)),
            ):
                try:
                    return func()
                except ImportError:
                    continue

        # Fallback to vision model
        return self.analyze_image(
            image_path,
            prompt="请提取并输出这张图片中的所有文字内容，保持原始格式。",
            max_tokens=2048,
        )

    @staticmethod
    def _ocr_with_paddleocr(image_path: str) -> str:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ImportError("未安装 PaddleOCR。请安装 requirements/ocr-paddle.txt。") from exc
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = ocr.ocr(image_path, cls=True)
        lines = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                lines.append(text)
        return "\n".join(lines)

    @staticmethod
    def _ocr_with_easyocr(image_path: str, gpu: bool = False) -> str:
        try:
            import easyocr
        except ImportError as exc:
            raise ImportError("未安装 EasyOCR。请安装 requirements/ocr-easyocr.txt。") from exc
        reader = easyocr.Reader(["ch_sim", "en"], gpu=gpu)
        results = reader.readtext(image_path)
        lines = [r[1] for r in results]
        return "\n".join(lines)

    def unload(self):
        import torch
        if self.model:
            del self.model
            self.model = None
        if self.processor:
            del self.processor
            self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in VisionRunner.SUPPORTED_IMAGE_FORMATS

    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """Convert image to base64 string (for API transport)."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
