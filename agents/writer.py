"""Writer Agent — chapter draft generation."""
from __future__ import annotations

import time
from typing import Any

from agents.base import format_memory_context, format_tone_block
from memory.schemas import ToneFingerprint
from utils.llm_client import invoke_text, load_prompt
from utils.logger import get_trace_logger


def run_writer(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    memory = state.get("memory", {})
    research = state.get("research_by_chapter", {}).get(chapter_num, {})
    trace = get_trace_logger(run_id)

    ch = next((c for c in outline.get("chapters", []) if c["chapter_number"] == chapter_num), {})
    tone_fp = memory.get("tone_fingerprint") or {"tone": brief.get("tone", "Conversational"), "rules": []}
    if state.get("tone_override"):
        tone_fp = {"tone": state["tone_override"], "rules": []}

    trace.log_agent_start("writer", {"chapter": chapter_num})
    start = time.perf_counter()

    target_words = ch.get("target_words", brief.get("words_per_chapter", 2500))
    prompt = load_prompt(
        "writer.txt",
        chapter_number=str(chapter_num),
        chapter_title=ch.get("title", ""),
        chapter_summary=ch.get("summary", ""),
        target_words=str(target_words),
        tone_block=format_tone_block(tone_fp),
        memory_context=format_memory_context(memory, chapter_num),
        facts=str(research.get("facts", []))[:8000],
        genre=brief.get("genre", "non-fiction"),
    )
    text = invoke_text("writer", prompt, tier="strong", run_id=run_id)
    word_count = len(text.split())

    chapters = list(state.get("chapters", []))
    existing = next((i for i, c in enumerate(chapters) if c.get("chapter_number") == chapter_num), None)
    entry = {
        "chapter_number": chapter_num,
        "title": ch.get("title", f"Chapter {chapter_num}"),
        "raw_text": text,
        "word_count": word_count,
    }
    if existing is not None:
        chapters[existing] = {**chapters[existing], **entry}
    else:
        chapters.append(entry)

    trace.log_agent_end("writer", {"word_count": word_count}, (time.perf_counter() - start) * 1000)
    return {"chapters": chapters}
