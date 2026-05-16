"""Memory Keeper — read/write cross-chapter memory."""
from __future__ import annotations

import json
import time
from typing import Any

from memory.memory_store import MemoryStore
from memory.schemas import (
    BookMemory,
    CallbackRecord,
    DecisionLogEntry,
    FactRecord,
    GlossaryTerm,
    ToneFingerprint,
)
from config import get_settings
from utils.llm_client import load_prompt
from utils.logger import get_trace_logger


def _load_tone_preset(tone: str) -> ToneFingerprint:
    settings = get_settings()
    path = settings.prompts_dir / "tonality" / f"{tone.lower()}.txt"
    rules: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                rules.append(line.lstrip("-• ").strip())
    if not rules:
        rules = [f"Write in {tone} voice throughout all surfaces."]
    return ToneFingerprint(tone=tone, rules=rules)


def run_memory_read(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    trace = get_trace_logger(run_id)
    store = MemoryStore(run_id)
    memory = store.load_memory()

    brief = state.get("brief", {})
    if memory.tone_fingerprint is None:
        memory.tone_fingerprint = _load_tone_preset(brief.get("tone", "Conversational"))

    read_keys = ["callback_index", "fact_registry", "character_bible", "tone_fingerprint"]
    trace.log_memory_io("memory_keeper", "read", memory_read=read_keys, details={"chapter": chapter_num})

    return {"memory": memory.model_dump()}


def run_memory_write(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    trace = get_trace_logger(run_id)
    store = MemoryStore(run_id)
    memory = BookMemory.model_validate(state.get("memory", {}))

    chapter = next((c for c in state.get("chapters", []) if c.get("chapter_number") == chapter_num), None)
    research = state.get("research_by_chapter", {}).get(chapter_num, {})

  # Extract facts from research
    for i, fact in enumerate(research.get("facts", [])):
        fid = f"F{chapter_num:03d}{i:02d}"
        memory.fact_registry.append(
            FactRecord(
                fact_id=fid,
                fact=fact.get("fact", str(fact)),
                source=fact.get("source", "retrieved_docs"),
                used_in=[chapter_num],
            )
        )

    for term in research.get("glossary_candidates", []):
        memory.glossary_terms.append(
            GlossaryTerm(
                term=term.get("term", ""),
                definition=term.get("definition", ""),
                introduced_in=chapter_num,
                chapter_refs=[chapter_num],
            )
        )

    if chapter:
        text = chapter.get("verified_text", chapter.get("edited_text", ""))
        if len(text) > 100:
            snippet = text[:120].replace("\n", " ")
            memory.callback_index.append(
                CallbackRecord(
                    callback_id=f"CB{chapter_num:03d}",
                    callback_text=snippet,
                    introduced_in=chapter_num,
                    used_in=[chapter_num],
                )
            )

    memory.decision_log.append(
        DecisionLogEntry(
            agent="memory_keeper",
            decision="chapter_memory_commit",
            rationale=f"Stored facts and callbacks for chapter {chapter_num}",
            chapter_ref=chapter_num,
        )
    )

    store.save_memory(memory)
    write_keys = ["fact_registry", "glossary_terms", "callback_index", "decision_log"]
    trace.log_memory_io("memory_keeper", "write", memory_write=write_keys, details={"chapter": chapter_num})

    store.save_snapshot(memory, state.get("outline"), state.get("chapters", []), state.get("brief"))

    return {"memory": memory.model_dump()}
