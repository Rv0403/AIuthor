"""Fact Checker — verify claims, soften or abstain."""
from __future__ import annotations

import time
from typing import Any

from utils.llm_client import invoke_text, load_prompt
from utils.logger import get_trace_logger


def run_fact_checker(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    research = state.get("research_by_chapter", {}).get(chapter_num, {})
    trace = get_trace_logger(run_id)

    chapters = list(state.get("chapters", []))
    ch = next((c for c in chapters if c.get("chapter_number") == chapter_num), None)
    if not ch:
        return {}

    trace.log_agent_start("fact_checker", {"chapter": chapter_num})
    start = time.perf_counter()

    prompt = load_prompt(
        "fact_checker.txt",
        chapter_text=ch.get("edited_text", ch.get("humanized_text", ""))[:8000],
        verified_facts=str(research.get("facts", []))[:4000],
        references=str(research.get("references", []))[:2000],
    )
    text = invoke_text("fact_checker", prompt, tier="cheap", run_id=run_id)

    idx = next(i for i, c in enumerate(chapters) if c.get("chapter_number") == chapter_num)
    chapters[idx]["verified_text"] = text

    trace.log_agent_end("fact_checker", {}, (time.perf_counter() - start) * 1000)
    return {"chapters": chapters}
