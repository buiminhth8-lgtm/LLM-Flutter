"""Fine-tune log helpers with API-safe redaction."""

from __future__ import annotations

from pathlib import Path

from llm_studio.security.redaction import redact_sensitive_text


def sanitize_finetune_log(message: str | None) -> str:
    text = redact_sensitive_text(message or "") or ""
    kept: list[str] = []
    for line in text.splitlines():
        lowered = line.lower()
        if line.startswith("Traceback ") or lowered.lstrip().startswith("file "):
            continue
        kept.append(line)
    sanitized = "\n".join(kept).strip()
    return sanitized or "训练日志已脱敏。"


class FineTuneLogWriter:
    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / "train.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, level: str, message: str, *, event_type: str | None = None, step: int | None = None) -> None:
        clean = sanitize_finetune_log(message)
        prefix = f"[{level}]"
        if event_type:
            prefix += f"[{event_type}]"
        if step is not None:
            prefix += f"[step={step}]"
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"{prefix} {clean}\n")
