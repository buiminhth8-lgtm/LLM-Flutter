"""Stable text diff generation for Novel Studio revisions."""

from __future__ import annotations

import difflib
from typing import Literal


class TextDiffService:
    """Build deterministic line/character diffs using Python's standard library."""

    def build_diff(self, original_text: str, edited_text: str) -> dict:
        original = original_text or ""
        edited = edited_text or ""
        mode: Literal["chars", "lines"] = "lines" if self._use_line_diff(original, edited) else "chars"
        original_units = self._units(original, mode)
        edited_units = self._units(edited, mode)
        matcher = difflib.SequenceMatcher(None, original_units, edited_units, autojunk=False)

        ops: list[dict[str, str]] = []
        added_chars = 0
        removed_chars = 0
        changed_blocks = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            original_segment = "".join(original_units[i1:i2])
            edited_segment = "".join(edited_units[j1:j2])
            if tag == "equal":
                self._append_op(ops, "equal", original_segment)
                continue
            changed_blocks += 1
            if tag in {"replace", "delete"} and original_segment:
                removed_chars += len(original_segment)
                self._append_op(ops, "delete", original_segment)
            if tag in {"replace", "insert"} and edited_segment:
                added_chars += len(edited_segment)
                self._append_op(ops, "insert", edited_segment)

        return {
            "format": "line_word_v1",
            "summary": {
                "original_chars": len(original),
                "edited_chars": len(edited),
                "added_chars": added_chars,
                "removed_chars": removed_chars,
                "changed_blocks": changed_blocks,
            },
            "ops": ops,
        }

    @staticmethod
    def _use_line_diff(original: str, edited: str) -> bool:
        return len(original) + len(edited) > 6000 or "\n" in original or "\n" in edited

    @staticmethod
    def _units(text: str, mode: Literal["chars", "lines"]) -> list[str]:
        if mode == "lines":
            lines = text.splitlines(keepends=True)
            return lines if lines else ([text] if text else [])
        return list(text)

    @staticmethod
    def _append_op(ops: list[dict[str, str]], op_type: str, text: str) -> None:
        if not text:
            return
        if ops and ops[-1]["type"] == op_type:
            ops[-1]["text"] += text
        else:
            ops.append({"type": op_type, "text": text})
