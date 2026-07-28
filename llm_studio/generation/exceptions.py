"""Generation worker exceptions."""


class GenerationError(RuntimeError):
    """Base generation error."""


class GenerationTimeoutError(GenerationError):
    """Raised when generation exceeds its timeout."""


class GenerationCancelledError(GenerationError):
    """Raised when generation is cancelled."""


class CudaOutOfMemoryError(GenerationError):
    """Raised when CUDA reports out of memory."""


def map_generation_exception(exc: BaseException) -> GenerationError:
    message = str(exc)
    if "CUDA out of memory" in message or "out of memory" in message.lower():
        return CudaOutOfMemoryError(
            "当前显存不足，建议：1. 降低上下文长度；2. 减少 max_new_tokens；"
            "3. 使用 4bit 或 GGUF；4. 卸载其他 GPU 模型。"
        )
    if isinstance(exc, GenerationError):
        return exc
    return GenerationError(message)
