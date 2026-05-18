"""Pick chapter pipeline depth from estimated context size."""
from __future__ import annotations

from typing import Any, Literal

from config import get_settings
from utils.token_tracker import estimate_tokens_from_text

ChapterPipelineMode = Literal["batch", "combined", "split"]


def _words_per_chapter(state: dict[str, Any]) -> int:
    brief = state.get("brief", {})
    outline = state.get("outline", {})
    chs = outline.get("chapters", [])
    if chs:
        return int(chs[0].get("target_words", brief.get("words_per_chapter", 2500)))
    return int(brief.get("words_per_chapter", 2500))


def _total_chapters(state: dict[str, Any]) -> int:
    return int(state.get("total_chapters") or len(state.get("outline", {}).get("chapters", [])) or 1)


def estimate_combined_chapter_input_tokens(state: dict[str, Any], chapter_num: int) -> int:
    """Rough input size for one combined chapter pass."""
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    memory = state.get("memory", {})
    ch = next((c for c in outline.get("chapters", []) if c["chapter_number"] == chapter_num), {})
    parts = [
        str(brief),
        str(ch),
        str(memory)[:4000],
        "x" * 3000,  # RAG / facts allowance
    ]
    return estimate_tokens_from_text("\n".join(parts))


def estimate_batch_input_tokens(state: dict[str, Any]) -> int:
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    memory = state.get("memory", {})
    n = _total_chapters(state)
    w = _words_per_chapter(state)
    parts = [str(brief), str(outline), str(memory)[:4000], "x" * (2500 * n)]
    base = estimate_tokens_from_text("\n".join(parts))
    return base + n * (w // 2)


def estimate_batch_output_tokens(state: dict[str, Any]) -> int:
    n = _total_chapters(state)
    w = _words_per_chapter(state)
    return int(n * w * 1.35)


def choose_chapter_pipeline_mode(state: dict[str, Any]) -> ChapterPipelineMode:
    """
    batch     — all chapters in one LLM call (small books)
    combined  — research+write+polish+facts in one call per chapter (default for most)
    split     — separate agent per step (only when one combined chapter won't fit)
    """
    settings = get_settings()
    forced = getattr(settings, "chapter_pipeline_mode", "auto")
    if forced in ("batch", "combined", "split"):
        return forced  # type: ignore[return-value]

    n = _total_chapters(state)
    w = _words_per_chapter(state)
    max_in = settings.groq_strong_max_input_tokens - 800
    max_out_reserve = 2500

    batch_in = estimate_batch_input_tokens(state)
    batch_out = estimate_batch_output_tokens(state)
    if n <= settings.batch_chapters_max and batch_in + (batch_out // 4) < max_in - max_out_reserve:
        return "batch"

    combined_in = estimate_combined_chapter_input_tokens(state, 1)
    combined_out = int(w * 1.35)
    if combined_in + combined_out < max_in:
        return "combined"

    if combined_in > max_in * 2:
        return "split"

    return "combined"
