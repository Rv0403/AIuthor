"""Researcher Agent — RAG-grounded facts per chapter."""
from __future__ import annotations

import json
import time
from typing import Any

from memory.schemas import ChapterResearch
from rag.retriever import RAGRetriever
from utils.llm_client import invoke_structured, load_prompt
from utils.logger import get_trace_logger


def run_researcher(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    trace = get_trace_logger(run_id)

    ch = next((c for c in outline.get("chapters", []) if c["chapter_number"] == chapter_num), None)
    if not ch:
        return {}

    trace.log_agent_start("researcher", {"chapter": chapter_num})
    start = time.perf_counter()

    collection = f"run_{run_id}" if run_id else "default"
    retriever = RAGRetriever(collection)
    query = f"{brief.get('topic', '')} {ch.get('title', '')} {ch.get('summary', '')}"
    retrieved = retriever.retrieve(query)
    context = "\n\n---\n\n".join(r["text"] for r in retrieved) if retrieved else "No retrieved documents."

    prompt = load_prompt(
        "researcher.txt",
        topic=brief.get("topic", ""),
        chapter_title=ch.get("title", ""),
        chapter_summary=ch.get("summary", ""),
        tone=brief.get("tone", "Conversational"),
        retrieved_context=context[:12000],
    )
    research = invoke_structured("researcher", prompt, ChapterResearch, tier="cheap", run_id=run_id)
    research_dict = research.model_dump()
    research_dict["chapter_number"] = chapter_num
    research_dict["retrieved_sources"] = [r.get("metadata", {}) for r in retrieved]

    research_by = dict(state.get("research_by_chapter", {}))
    research_by[chapter_num] = research_dict

    trace.log_agent_end("researcher", {"facts": len(research.facts)}, (time.perf_counter() - start) * 1000)

    return {"research_by_chapter": research_by}
