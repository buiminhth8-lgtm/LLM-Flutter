"""Fine-tuning module - supports LoRA and QLoRA fine-tuning."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .chat import build_model_input
from .finetune.memory_estimator import estimate_training_memory
from .runtime.capabilities import detect_runtime_capabilities
from .runtime.model_load_policy import estimate_model_size_b


@dataclass
class FineTuneArgs:
    """Fine-tuning arguments tuned for low VRAM GPUs by default."""

    model_path: str = ""
    dataset_path: str = ""
    output_dir: str = ""
    method: str = "qlora"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: str | list[str] = "all-linear"
    learning_rate: float = 2e-4
    num_epochs: int = 3
    per_device_train_batch_size: int = 1
    batch_size: int = 1
    gradient_accumulation_steps: int = 16
    warmup_ratio: float = 0.03
    max_seq_length: int = 1024
    save_steps: int = 100
    logging_steps: int = 5
    gradient_checkpointing: bool = True
    precision: str = "auto"
    fp16: bool = False
    bf16: bool = False
    resume_from_checkpoint: str | bool | None = None

    @classmethod
    def from_config(cls, config_dict: dict, **overrides) -> "FineTuneArgs":
        """Create from config dict with optional overrides."""
        merged = {**config_dict, **overrides}
        valid_fields = {name for name in cls.__dataclass_fields__}
        filtered = {key: value for key, value in merged.items() if key in valid_fields}
        return cls(**filtered)


class DatasetProcessor:
    """Process datasets into the format needed for fine-tuning."""

    @staticmethod
    def load_dataset(path: str, format: str = "auto") -> list[dict]:
        p = Path(path)
        if format == "auto":
            format = "json" if p.suffix == ".json" else "jsonl"

        data = []
        if format == "jsonl":
            with open(path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        data.append(json.loads(line))
        elif format == "json":
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                data = data.get("data", data.get("items", [data]))
        return data

    @staticmethod
    def item_to_messages(item: dict) -> list[dict[str, str]]:
        if "conversations" in item:
            messages: list[dict[str, str]] = []
            for conv in item["conversations"]:
                role = conv.get("from", conv.get("role", "user"))
                content = conv.get("value", conv.get("content", ""))
                if role in ("human", "user"):
                    messages.append({"role": "user", "content": content})
                elif role in ("gpt", "assistant"):
                    messages.append({"role": "assistant", "content": content})
                elif role == "system":
                    messages.insert(0, {"role": "system", "content": content})
            return messages

        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output_text = item.get("output", "")
        user_msg = f"{instruction}\n\n{input_text}" if input_text else instruction
        return [
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": output_text},
        ]


def tokenize_messages_for_assistant_loss(
    tokenizer,
    messages: list[dict[str, str]],
    max_seq_length: int,
) -> dict:
    """Tokenize a conversation and mask non-assistant tokens with -100."""
    full_text = build_model_input(tokenizer, messages, add_generation_prompt=False)
    input_ids = tokenizer(
        full_text,
        truncation=True,
        max_length=max_seq_length,
        add_special_tokens=False,
    )["input_ids"]

    labels = [-100] * len(input_ids)
    for idx, msg in enumerate(messages):
        if msg["role"] != "assistant":
            continue
        prefix_text = build_model_input(tokenizer, messages[:idx], add_generation_prompt=True)
        end_text = build_model_input(tokenizer, messages[: idx + 1], add_generation_prompt=False)
        start = len(
            tokenizer(
                prefix_text,
                truncation=True,
                max_length=max_seq_length,
                add_special_tokens=False,
            )["input_ids"]
        )
        end = len(
            tokenizer(
                end_text,
                truncation=True,
                max_length=max_seq_length,
                add_special_tokens=False,
            )["input_ids"]
        )
        for pos in range(min(start, len(input_ids)), min(end, len(input_ids))):
            labels[pos] = input_ids[pos]

    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": labels,
    }


class DynamicAssistantDataCollator:
    """Dynamically pad batch tensors and keep padding labels at -100."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features: list[dict]):
        import torch

        max_len = max(len(feature["input_ids"]) for feature in features)
        pad_id = self.tokenizer.pad_token_id
        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for feature in features:
            pad_len = max_len - len(feature["input_ids"])
            batch["input_ids"].append(feature["input_ids"] + [pad_id] * pad_len)
            batch["attention_mask"].append(feature["attention_mask"] + [0] * pad_len)
            batch["labels"].append(feature["labels"] + [-100] * pad_len)
        return {key: torch.tensor(value, dtype=torch.long) for key, value in batch.items()}


class FineTuner:
    """Fine-tune LLMs using LoRA / QLoRA."""

    def __init__(self, args: FineTuneArgs):
        self.args = args
        self.model = None
        self.tokenizer = None
        self.trainer = None

    def _precision_flags(self) -> tuple[bool, bool]:
        caps = detect_runtime_capabilities(run_bnb_probe=False)
        if self.args.precision == "bf16":
            return False, True
        if self.args.precision == "fp16":
            return True, False
        if self.args.precision == "auto":
            return (False, True) if caps.bf16_supported else (True, False)
        return self.args.fp16, self.args.bf16

    def estimate_training_risk(self) -> list[str]:
        warnings: list[str] = []
        size_b = estimate_model_size_b(self.args.model_path)
        estimate = estimate_training_memory(
            model_path=self.args.model_path,
            method=self.args.method,
            max_seq_length=self.args.max_seq_length,
            batch_size=self.args.per_device_train_batch_size or self.args.batch_size,
        )
        if estimate.risk_level == "unsupported":
            raise RuntimeError(estimate.message)
        if estimate.risk_level in {"warning", "high-risk"}:
            warnings.append(estimate.message)
        if size_b is None:
            return warnings
        if size_b >= 14:
            raise RuntimeError("14B 及以上模型默认不允许在 8GB 显存上微调，请明确改用更小模型或外部训练环境。")
        if size_b >= 6.5:
            warnings.append("7B/8B 模型在 8GB 显存上仅建议 QLoRA、batch=1、短上下文，并仍有 OOM 风险。")
        return warnings

    def prepare_model(self):
        """Load and prepare model for fine-tuning."""
        import torch
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer

        fp16, bf16 = self._precision_flags()
        self.args.fp16 = fp16
        self.args.bf16 = bf16

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.args.model_path,
            trust_remote_code=False,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        quant_config = None
        if self.args.method == "qlora":
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise RuntimeError("当前未安装 QLoRA/bitsandbytes 后端。请安装 requirements/cuda.txt。") from exc
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16 if bf16 else torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )

        load_kwargs = {
            "pretrained_model_name_or_path": self.args.model_path,
            "trust_remote_code": False,
            "device_map": "auto",
            "low_cpu_mem_usage": True,
        }
        if quant_config:
            load_kwargs["quantization_config"] = quant_config
        load_kwargs["torch_dtype"] = torch.bfloat16 if bf16 else torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
        if hasattr(self.model, "config"):
            self.model.config.use_cache = False
        if self.args.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        if self.args.method == "qlora":
            self.model = prepare_model_for_kbit_training(self.model)

        lora_config = LoraConfig(
            r=self.args.lora_r,
            lora_alpha=self.args.lora_alpha,
            lora_dropout=self.args.lora_dropout,
            target_modules=self.args.target_modules,
            bias="none",
            task_type="CAUSAL_LM",
        )
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

    def prepare_dataset(self, dataset_path: str):
        """Load and prepare the training dataset."""
        from datasets import Dataset

        raw_data = DatasetProcessor.load_dataset(dataset_path)
        tokenized_rows = [
            tokenize_messages_for_assistant_loss(
                self.tokenizer,
                DatasetProcessor.item_to_messages(item),
                self.args.max_seq_length,
            )
            for item in raw_data
        ]
        return Dataset.from_list(tokenized_rows)

    def train(
        self,
        dataset_path: str,
        progress_callback: Optional[Callable] = None,
        resume_from_checkpoint: str | bool | None = None,
    ) -> str:
        """Run the fine-tuning training loop."""
        from transformers import Trainer, TrainerCallback, TrainingArguments

        for warning in self.estimate_training_risk():
            print(f"[FineTune] Warning: {warning}")

        self.prepare_model()
        train_dataset = self.prepare_dataset(dataset_path)
        output_dir = self.args.output_dir
        os.makedirs(output_dir, exist_ok=True)

        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=self.args.num_epochs,
            per_device_train_batch_size=self.args.per_device_train_batch_size or self.args.batch_size,
            gradient_accumulation_steps=self.args.gradient_accumulation_steps,
            learning_rate=self.args.learning_rate,
            warmup_ratio=self.args.warmup_ratio,
            logging_steps=self.args.logging_steps,
            save_steps=self.args.save_steps,
            save_total_limit=3,
            fp16=self.args.fp16,
            bf16=self.args.bf16,
            gradient_checkpointing=self.args.gradient_checkpointing,
            optim="paged_adamw_8bit" if self.args.method == "qlora" else "adamw_torch",
            report_to="none",
            remove_unused_columns=False,
        )

        callbacks = []
        if progress_callback:

            class ProgressCallback(TrainerCallback):
                def on_log(self, args, state, control, logs=None, **kwargs):
                    if logs and state.global_step > 0:
                        progress_callback(
                            {
                                "step": state.global_step,
                                "max_steps": state.max_steps,
                                "loss": logs.get("loss", 0),
                                "learning_rate": logs.get("learning_rate", 0),
                                "epoch": logs.get("epoch", 0),
                            }
                        )

            callbacks.append(ProgressCallback())

        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=DynamicAssistantDataCollator(self.tokenizer),
            callbacks=callbacks,
        )

        checkpoint = resume_from_checkpoint or self.args.resume_from_checkpoint
        self.trainer.train(resume_from_checkpoint=checkpoint)

        final_path = os.path.join(output_dir, "final")
        self.model.save_pretrained(final_path)
        self.tokenizer.save_pretrained(final_path)
        return final_path

    def merge_and_save(self, output_path: str) -> str:
        """Merge LoRA weights into the base model and save."""
        self.model.merge_and_unload().save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        return output_path
