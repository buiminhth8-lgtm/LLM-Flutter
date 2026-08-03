"""LoRA trainer implementation for Stage 8."""

from __future__ import annotations

from typing import Any

from llm_studio.finetuner import FineTuneArgs, FineTuner

from .trainer import CancellationToken, FineTuneCallbacks, FineTuneTrainerResult


class LoraFineTuneTrainer:
    def run(
        self,
        run: dict[str, Any],
        config: dict[str, Any],
        dataset_paths: dict[str, str | None],
        callbacks: FineTuneCallbacks,
        cancellation_token: CancellationToken,
    ) -> FineTuneTrainerResult:
        cancellation_token.throw_if_cancelled()
        callbacks.on_log("info", "LoRA trainer is loading model and tokenizer.", "start")
        args = FineTuneArgs.from_config(
            config,
            method="lora",
            model_path=str(config["model_path"]),
            dataset_path=str(dataset_paths["train"]),
            output_dir=str(config["adapter_output_dir"]),
            resume_from_checkpoint=config.get("resume_from_checkpoint_path"),
        )
        tuner = FineTuner(args)

        def progress(payload: dict[str, Any]) -> None:
            cancellation_token.throw_if_cancelled()
            step = int(payload.get("step") or 0)
            callbacks.on_train_metrics(
                step,
                {
                    "epoch": payload.get("epoch"),
                    "train_loss": payload.get("loss"),
                    "learning_rate": payload.get("learning_rate"),
                },
            )

        adapter_path = tuner.train(
            str(dataset_paths["train"]),
            progress_callback=progress,
            resume_from_checkpoint=config.get("resume_from_checkpoint_path"),
        )
        cancellation_token.throw_if_cancelled()
        callbacks.on_checkpoint(
            int(config.get("total_steps") or 0),
            adapter_path,
            {"checkpoint_type": "last"},
        )
        callbacks.on_log("info", "LoRA trainer completed.", "done")
        return FineTuneTrainerResult(
            adapter_path=adapter_path,
            final_step=int(config.get("total_steps") or 0),
        )
