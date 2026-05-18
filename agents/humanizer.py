"""Humanizer Agent — remove AI tells, add voice."""
from __future__ import annotations

import time
from typing import Any

from agents.base import format_memory_context, format_tone_block
from config import get_settings
from utils.llm_client import invoke_text, load_prompt
from utils.logger import get_trace_logger


def run_humanizer(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    memory = state.get("memory", {})
    brief = state.get("brief", {})
    trace = get_trace_logger(run_id)

    chapters = list(state.get("chapters", []))
    ch = next((c for c in chapters if c.get("chapter_number") == chapter_num), None)
    if not ch:
        return {}

    trace.log_agent_start("humanizer", {"chapter": chapter_num})
    start = time.perf_counter()

    tone_fp = memory.get("tone_fingerprint") or {"tone": brief.get("tone", "Conversational")}
    if state.get("tone_override"):
        tone_fp = {"tone": state["tone_override"], "rules": []}

    raw = ch.get("raw_text", "")[:10000]
    prompt = load_prompt(
        "humanizer.txt",
        chapter_text=raw,
        tone_block=format_tone_block(tone_fp),
        memory_context=format_memory_context(memory, chapter_num),
    )
    settings = get_settings()
    if settings.humanizer_variants and not settings.mock_llm:
        from evals.tone_eval import pick_best_opening

        tone_name = (
            tone_fp.get("tone", brief.get("tone", "Conversational"))
            if isinstance(tone_fp, dict)
            else brief.get("tone", "Conversational")
        )
        full_a = invoke_text("humanizer", prompt, tier="strong", run_id=run_id)
        variant_b = invoke_text(
            "humanizer",
            prompt + "\n\nUse a bolder, more surprising opening hook.",
            tier="strong",
            run_id=run_id,
        )
        text, _ = pick_best_opening([full_a, variant_b], tone_name, run_id)
    else:
        text = invoke_text("humanizer", prompt, tier="strong", run_id=run_id)

    idx = next(i for i, c in enumerate(chapters) if c.get("chapter_number") == chapter_num)
    chapters[idx]["humanized_text"] = text

    trace.log_agent_end("humanizer", {"chars": len(text)}, (time.perf_counter() - start) * 1000)
    return {"chapters": chapters}
