"""LangGraph node wrappers."""
from __future__ import annotations

import uuid
from typing import Any

from agents import (
    run_assembler,
    run_editor,
    run_fact_checker,
    run_humanizer,
    run_intent_analyzer,
    run_memory_read,
    run_memory_write,
    run_planner,
    run_researcher,
    run_writer,
)
from config import get_settings
from memory.memory_store import MemoryStore
from memory.repair import full_repair_after_insert
from memory.schemas import BookMemory
from rag.ingest import ingest_corpus


def node_intent(state: dict[str, Any]) -> dict[str, Any]:
    result = run_intent_analyzer(state)
    result["task_type"] = result.get("task_type", "generate_book")
    return result


def node_load_source(state: dict[str, Any]) -> dict[str, Any]:
    source_id = state.get("source_run_id") or state.get("intent", {}).get("source_run_id")
    if not source_id:
        runs = MemoryStore.list_runs()
        source_id = runs[0] if runs else None
    if not source_id:
        return {"errors": state.get("errors", []) + ["No source run found"]}

    snap = MemoryStore.load_snapshot(source_id)
    if not snap:
        return {"errors": state.get("errors", []) + [f"Snapshot not found: {source_id}"]}

    updates: dict[str, Any] = {
        "outline": snap.outline or {},
        "chapters": snap.chapters or [],
        "memory": snap.memory.model_dump(),
        "brief": snap.brief or state.get("brief", {}),
        "source_run_id": source_id,
        "total_chapters": len((snap.outline or {}).get("chapters", [])),
    }
    intent = state.get("intent", {})
    if state.get("task_type") == "tone_conversion":
        target = intent.get("target_chapter") or state.get("target_chapter") or 3
        updates["current_chapter"] = target
        updates["tone_override"] = intent.get("tone") or state.get("tone_override")
        updates["brief"] = {**updates["brief"], "tone": updates["tone_override"]}
    if state.get("task_type") == "insert_chapter":
        updates["insert_after"] = intent.get("insert_after") or state.get("insert_after") or 4
    return updates


def node_prepare_insert(state: dict[str, Any]) -> dict[str, Any]:
    insert_after = state.get("insert_after", 4)
    existing = state.get("outline", {}).get("chapters", [])
    if existing:
        max_ch = max(c["chapter_number"] for c in existing)
        insert_after = min(insert_after, max_ch)
    outline = state.get("outline", {})
    chapters = state.get("chapters", [])
    memory = BookMemory.model_validate(state.get("memory", {}))

    new_ch = {
        "title": f"New Chapter after {insert_after}",
        "summary": state.get("intent", {}).get("topic", "Bridging content"),
        "target_words": state.get("brief", {}).get("words_per_chapter", 2500),
    }
    memory, outline, chapters = full_repair_after_insert(memory, outline, chapters, insert_after, new_ch)
    return {
        "memory": memory.model_dump(),
        "outline": outline,
        "chapters": chapters,
        "current_chapter": insert_after + 1,
        "total_chapters": len(outline.get("chapters", [])),
    }


def node_planner(state: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    run_id = state.get("run_id") or str(uuid.uuid4())[:8]
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    ingest_corpus(f"run_{run_id}")
    return {"run_id": run_id, **run_planner(state)}


def node_chapter_pipeline(state: dict[str, Any]) -> dict[str, Any]:
    """Single chapter: research → memory read → write → humanize → edit → fact-check → memory write."""
    s = dict(state)
    for fn in (run_researcher, run_memory_read, run_writer, run_humanizer, run_editor, run_fact_checker, run_memory_write):
        s = {**s, **fn(s)}
    return s


def node_advance_chapter(state: dict[str, Any]) -> dict[str, Any]:
    current = state.get("current_chapter", 1)
    return {"current_chapter": current + 1}


def node_assembler(state: dict[str, Any]) -> dict[str, Any]:
    return run_assembler(state)


def node_init_generate(state: dict[str, Any]) -> dict[str, Any]:
    return {"current_chapter": 1, "chapters": [], "research_by_chapter": {}, "memory": {}}
