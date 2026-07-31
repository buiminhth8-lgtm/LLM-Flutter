"""Writing mode definitions and Prompt Studio mappings."""

from __future__ import annotations

GENERATION_MODES = frozenset(
    {
        "chapter_generate",
        "chapter_continue",
        "chapter_rewrite",
        "chapter_polish",
        "chapter_expand",
        "dialogue_enhance",
        "scene_expand",
        "summary_generate",
        "custom",
    }
)

_MODE_TEMPLATE_TYPES = {mode: mode for mode in GENERATION_MODES}


def mode_template_type(mode: str) -> str:
    """Return the recommended Prompt Studio template type for a mode."""

    return _MODE_TEMPLATE_TYPES[mode]
