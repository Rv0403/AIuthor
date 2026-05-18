"""Editor Agent — pacing, transitions, consistency."""
from __future__ import annotations

import time
from typing import Any

from utils.llm_client import invoke_text, load_prompt
from utils.logger import get_trace_logger


def run_editor(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    trace = get_trace_logger(run_id)

    chapters = list(state.get("chapters", []))
    ch = next((c for c in chapters if c.get("chapter_number") == chapter_num), None)
    if not ch:
        return {}

    trace.log_agent_start("editor", {"chapter": chapter_num})
    start = time.perf_counter()

    prompt = load_prompt(
        "editor.txt",
        chapter_text=ch.get("humanized_text", ch.get("raw_text", ""))[:10000],
        chapter_number=str(chapter_num),
        book_title=state.get("outline", {}).get("title", ""),
    )
    text = invoke_text("editor", prompt, tier="strong", run_id=run_id)

    idx = next(i for i, c in enumerate(chapters) if c.get("chapter_number") == chapter_num)
    chapters[idx]["edited_text"] = text

    trace.log_agent_end("editor", {}, (time.perf_counter() - start) * 1000)
    return {"chapters": chapters}
