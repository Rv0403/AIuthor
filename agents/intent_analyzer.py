"""Intent Analyzer — first agent; routes NL to structured task."""
from __future__ import annotations

import time
from typing import Any

from memory.schemas import IntentResult
from utils.llm_client import invoke_structured, load_prompt
from utils.logger import get_trace_logger


def run_intent_analyzer(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    trace = get_trace_logger(run_id) if run_id else None
    user_input = state.get("user_input", "")

    if trace:
        trace.log_agent_start("intent_analyzer", {"user_input": user_input[:500]})

    start = time.perf_counter()
    from config import get_settings
    from agents.intent_heuristics import parse_intent_heuristic

    heuristic = parse_intent_heuristic(user_input)
    if get_settings().mock_llm and heuristic:
        intent = heuristic
    else:
        prompt = load_prompt("intent_analyzer.txt", user_input=user_input)
        intent = invoke_structured("intent_analyzer", prompt, IntentResult, tier="cheap", run_id=run_id)
        if heuristic and not intent.source_run_id:
            intent.source_run_id = heuristic.source_run_id
            if heuristic.task_type != "generate_book":
                intent.task_type = heuristic.task_type
                intent.insert_after = heuristic.insert_after
                intent.target_chapter = heuristic.target_chapter

    if trace:
        trace.log_agent_end("intent_analyzer", intent.model_dump(), (time.perf_counter() - start) * 1000)

    return {
        "task_type": intent.task_type,
        "intent": intent.model_dump(),
        "brief": {
            "topic": intent.topic,
            "reader": intent.reader,
            "tone": intent.tone,
            "genre": intent.genre,
            "num_chapters": intent.num_chapters,
            "words_per_chapter": intent.words_per_chapter,
            "character_names": intent.character_names,
        },
        "source_run_id": intent.source_run_id,
        "insert_after": intent.insert_after,
        "target_chapter": intent.target_chapter,
        "tone_override": intent.tone if intent.task_type == "tone_conversion" else None,
    }
