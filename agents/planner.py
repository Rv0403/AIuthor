"""Planner Agent — book outline and structure."""
from __future__ import annotations

import time
from typing import Any

from config import get_settings
from memory.schemas import BookOutline, ChapterOutline
from utils.llm_client import invoke_structured, load_prompt
from utils.logger import get_trace_logger


def run_planner(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    brief = state.get("brief", {})
    trace = get_trace_logger(run_id)
    settings = get_settings()

    trace.log_agent_start("planner", brief)
    start = time.perf_counter()

    prompt = load_prompt(
        "planner.txt",
        topic=brief.get("topic", ""),
        reader=brief.get("reader", ""),
        tone=brief.get("tone", "Conversational"),
        genre=brief.get("genre", "non-fiction"),
        num_chapters=str(brief.get("num_chapters", 10)),
        words_per_chapter=str(brief.get("words_per_chapter", 2500)),
        character_names=", ".join(brief.get("character_names", [])) or "none",
    )

    outline = invoke_structured("planner", prompt, BookOutline, tier="strong", run_id=run_id)
    if settings.mock_llm:
        n = int(brief.get("num_chapters", 10))
        w = int(brief.get("words_per_chapter", 500))
        topic = brief.get("topic", "Personal Finance")
        outline = BookOutline(
            title="Money Made Simple",
            subtitle=f"A Beginner's Guide to {topic}",
            genre=brief.get("genre", "non-fiction"),
            chapters=[
                ChapterOutline(
                    chapter_number=i,
                    title=f"Chapter {i}: {topic} Fundamentals Part {i}",
                    summary=f"Core concepts for {topic} — section {i}",
                    target_words=w,
                )
                for i in range(1, n + 1)
            ],
        )
    outline_dict = outline.model_dump()

    trace.log_agent_end("planner", {"title": outline.title, "chapters": len(outline.chapters)}, (time.perf_counter() - start) * 1000)

    from utils.context_budget import choose_chapter_pipeline_mode

    planned = {
        "outline": outline_dict,
        "total_chapters": len(outline.chapters),
        "current_chapter": 1,
        "brief": brief,
    }
    mode = settings.chapter_pipeline_mode
    if mode == "auto":
        mode = choose_chapter_pipeline_mode({**state, **planned})
    planned["chapter_pipeline_mode"] = mode
    return planned
