"""Model runner - supports Transformers and llama.cpp (GGUF) backends."""

from __future__ import annotations

import time
from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Generator

from .chat import Message, build_model_input, normalize_messages, truncate_messages
from .config import Config
from .runtime.capabilities import detect_llama_cpp_cuda, detect_runtime_capabilities
from .runtime.device_info import auto_cpu_threads
from .runtime.model_load_policy import (
    choose_model_load_policy,
    generation_defaults,
)


class GenerationWorkerError(RuntimeError):
    """Raised when a background generation worker fails."""


class BaseRunner:
    """Base class for model runners."""

    def __init__(self, model_path: str, config: Config):
        self.model_path = model_path
        self.config = config
        self.model = None
        self.tokenizer = None
        self.load_policy = None

    def load(self):
        raise NotImplementedError

    def generate(self, prompt: str | list[Message], **kwargs) -> str:
        raise NotImplementedError

    def generate_stream(self, prompt: str | list[Message], **kwargs) -> Generator[str, None, None]:
        raise NotImplementedError

    def unload(self):
        raise NotImplementedError


class TransformersRunner(BaseRunner):
    """Run models using HuggingFace Transformers."""

    def load(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        capabilities = detect_runtime_capabilities()
        policy = choose_model_load_policy(self.model_path, self.config, capabilities)
        self.load_policy = policy

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=policy.trust_remote_code,
        )
        if getattr(self.tokenizer, "pad_token", None) is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        load_kwargs: dict[str, Any] = {
            "pretrained_model_name_or_path": self.model_path,
            "low_cpu_mem_usage": True,
            "trust_remote_code": policy.trust_remote_code,
        }

        if policy.device != "cpu":
            load_kwargs["device_map"] = "auto"
            load_kwargs["max_memory"] = policy.max_memory
            if policy.cpu_offload:
                offload_folder = self.config.runtime.get("offload_folder", "./cache/offload")
                Path(offload_folder).mkdir(parents=True, exist_ok=True)
                load_kwargs["offload_folder"] = offload_folder

        if policy.dtype == "bfloat16":
            load_kwargs["torch_dtype"] = torch.bfloat16
        elif policy.dtype == "float16":
            load_kwargs["torch_dtype"] = torch.float16
        elif policy.dtype == "float32":
            load_kwargs["torch_dtype"] = torch.float32

        if policy.attention_backend in {"sdpa", "eager"}:
            load_kwargs["attn_implementation"] = policy.attention_backend

        if policy.quantization in {"bnb4", "4bit"}:
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise RuntimeError(
                    "当前未安装 bitsandbytes 4-bit 后端。请安装 requirements/cuda.txt。"
                ) from exc
            load_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16
                if capabilities.bf16_supported
                else torch.float16,
            )

        try:
            self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
        except (TypeError, ValueError) as exc:
            if "attn_implementation" not in str(exc):
                raise
            load_kwargs["attn_implementation"] = "eager"
            self.load_policy = type(policy)(
                device=policy.device,
                dtype=policy.dtype,
                quantization=policy.quantization,
                attention_backend="eager",
                max_memory=policy.max_memory,
                cpu_offload=policy.cpu_offload,
                trust_remote_code=policy.trust_remote_code,
            )
            self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)

        if policy.device == "cpu":
            self.model = self.model.to("cpu")
        self.model.eval()

    def _prepare_inputs(self, messages: str | list[Message], max_context_tokens: int):
        normalized = normalize_messages(messages)
        normalized = truncate_messages(
            self.tokenizer,
            normalized,
            max_context_tokens=max_context_tokens,
        )
        text = build_model_input(self.tokenizer, normalized, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt")
        device = getattr(self.model, "device", None)
        if device is not None:
            inputs = inputs.to(device)
        return inputs

    def _generation_kwargs(self, kwargs: dict) -> dict:
        defaults = generation_defaults(self.config)
        temperature = kwargs.get("temperature", defaults["temperature"])
        return {
            "max_new_tokens": int(kwargs.get("max_tokens", kwargs.get("max_new_tokens", defaults["max_new_tokens"]))),
            "temperature": temperature,
            "top_p": kwargs.get("top_p", defaults["top_p"]),
            "top_k": kwargs.get("top_k", defaults["top_k"]),
            "repetition_penalty": kwargs.get("repetition_penalty", defaults["repetition_penalty"]),
            "do_sample": bool(kwargs.get("do_sample", defaults["do_sample"])) and temperature > 0,
        }

    def generate(self, prompt: str | list[Message], **kwargs) -> str:
        import torch

        defaults = generation_defaults(self.config)
        inputs = self._prepare_inputs(prompt, int(kwargs.get("max_context_tokens", defaults["max_context_tokens"])))
        gen_kwargs = self._generation_kwargs(kwargs)

        with torch.inference_mode():
            outputs = self.model.generate(**inputs, **gen_kwargs)

        new_tokens = outputs[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)

    def generate_stream(self, prompt: str | list[Message], **kwargs) -> Generator[str, None, None]:
        import torch
        from transformers import StoppingCriteria, StoppingCriteriaList, TextIteratorStreamer

        class CancelCriteria(StoppingCriteria):
            def __init__(self, event: Event):
                self.event = event

            def __call__(self, input_ids, scores, **kwargs):
                return self.event.is_set()

        defaults = generation_defaults(self.config)
        timeout = float(kwargs.get("timeout", self.config.runtime.get("request_timeout_seconds", 300)))
        started_at = time.monotonic()
        cancel_event = Event()
        errors: Queue[BaseException] = Queue(maxsize=1)

        inputs = self._prepare_inputs(prompt, int(kwargs.get("max_context_tokens", defaults["max_context_tokens"])))
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
            timeout=1.0,
        )
        generation_kwargs = {
            **inputs,
            **self._generation_kwargs(kwargs),
            "streamer": streamer,
            "stopping_criteria": StoppingCriteriaList([CancelCriteria(cancel_event)]),
        }

        def worker():
            try:
                with torch.inference_mode():
                    self.model.generate(**generation_kwargs)
            except BaseException as exc:
                try:
                    errors.put_nowait(exc)
                except Exception:
                    pass

        thread = Thread(target=worker, name="llm-studio-generation", daemon=True)
        thread.start()
        try:
            while thread.is_alive():
                try:
                    chunk = next(streamer)
                    if chunk:
                        yield chunk
                except StopIteration:
                    break
                except Empty:
                    if not thread.is_alive():
                        break
                if errors.qsize():
                    raise GenerationWorkerError(str(errors.get_nowait()))
                if timeout > 0 and time.monotonic() - started_at > timeout:
                    cancel_event.set()
                    raise TimeoutError(f"生成超时，超过 {timeout:.0f} 秒。")
            for chunk in streamer:
                if chunk:
                    yield chunk
            if errors.qsize():
                raise GenerationWorkerError(str(errors.get_nowait()))
        except GeneratorExit:
            cancel_event.set()
            raise
        finally:
            cancel_event.set()
            thread.join(timeout=5)

    def unload(self):
        import torch

        self.model = None
        self.tokenizer = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class GGUFRunner(BaseRunner):
    """Run GGUF models using llama-cpp-python."""

    def load(self):
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "当前未安装 GGUF 后端。请安装 requirements/gguf.txt。"
            ) from exc

        cuda_enabled, detail = detect_llama_cpp_cuda()
        llama_cfg = self.config.get("llama_cpp", {})
        n_threads = int(llama_cfg.get("n_threads", 0) or 0)
        if n_threads <= 0:
            n_threads = auto_cpu_threads()

        n_gpu_layers = int(llama_cfg.get("n_gpu_layers", -1))
        if n_gpu_layers != 0 and not cuda_enabled:
            print("[GGUF] llama-cpp-python 当前不是 CUDA 构建，将以 CPU 模式运行。")
            print(f"[GGUF] 构建信息: {detail}")

        self.model = Llama(
            model_path=self.model_path,
            n_ctx=int(llama_cfg.get("n_ctx", 4096)),
            n_gpu_layers=n_gpu_layers if cuda_enabled else 0,
            n_batch=int(llama_cfg.get("n_batch", 256)),
            n_ubatch=int(llama_cfg.get("n_ubatch", 128)),
            n_threads=n_threads,
            flash_attn=bool(llama_cfg.get("flash_attn", True)),
            offload_kqv=bool(llama_cfg.get("offload_kqv", True)),
            verbose=True,
        )
        print(f"[GGUF] CUDA enabled: {cuda_enabled}; n_gpu_layers={n_gpu_layers if cuda_enabled else 0}")

    def generate(self, prompt: str | list[Message], **kwargs) -> str:
        defaults = generation_defaults(self.config)
        messages = normalize_messages(prompt)
        response = self.model.create_chat_completion(
            messages=messages,
            max_tokens=int(kwargs.get("max_tokens", defaults["max_new_tokens"])),
            temperature=kwargs.get("temperature", defaults["temperature"]),
            top_p=kwargs.get("top_p", defaults["top_p"]),
            top_k=kwargs.get("top_k", defaults["top_k"]),
            repeat_penalty=kwargs.get("repetition_penalty", defaults["repetition_penalty"]),
        )
        return response["choices"][0]["message"]["content"]

    def generate_stream(self, prompt: str | list[Message], **kwargs) -> Generator[str, None, None]:
        defaults = generation_defaults(self.config)
        stream = self.model.create_chat_completion(
            messages=normalize_messages(prompt),
            max_tokens=int(kwargs.get("max_tokens", defaults["max_new_tokens"])),
            temperature=kwargs.get("temperature", defaults["temperature"]),
            top_p=kwargs.get("top_p", defaults["top_p"]),
            top_k=kwargs.get("top_k", defaults["top_k"]),
            repeat_penalty=kwargs.get("repetition_penalty", defaults["repetition_penalty"]),
            stream=True,
        )
        try:
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
        except GeneratorExit:
            raise

    def unload(self):
        self.model = None


def create_runner(model_path: str, config: Config) -> BaseRunner:
    """Factory function to create the appropriate model runner."""
    p = Path(model_path)
    backend = config.runtime.get("backend", "auto")
    if backend == "gguf" or p.suffix == ".gguf" or (p.is_file() and ".gguf" in p.name.lower()):
        return GGUFRunner(model_path, config)
    return TransformersRunner(model_path, config)
