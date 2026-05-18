"""Adaptive chapter processing — batch, combined, or split by context size."""
from __future__ import annotations

import time
from typing import Any

from agents.base import format_memory_context, format_tone_block
from agents.editor import run_editor
from agents.fact_checker import run_fact_checker
from agents.humanizer import run_humanizer
from agents.memory_keeper import run_memory_read, run_memory_write
from agents.researcher import run_researcher
from agents.writer import run_writer
from config import get_settings
from memory.schemas import BatchChapterItem, ChaptersBatchOutput, ChapterResearch
from rag.retriever import RAGRetriever
from utils.context_budget import choose_chapter_pipeline_mode
from utils.llm_client import invoke_structured, invoke_text, load_prompt
from utils.logger import get_trace_logger


def _rag_facts_for_chapter(
    run_id: str, brief: dict[str, Any], ch: dict[str, Any]
) -> tuple[list[dict[str, str]], str]:
    collection = f"run_{run_id}" if run_id else "default"
    retriever = RAGRetriever(collection)
    query = f"{brief.get('topic', '')} {ch.get('title', '')} {ch.get('summary', '')}"
    retrieved = retriever.retrieve(query)
    facts = [
        {
            "fact": (r.get("text") or "")[:600],
            "source": (r.get("metadata") or {}).get("source", "corpus"),
        }
        for r in (retrieved or [])[:5]
    ]
    context = "\n\n---\n\n".join(r["text"] for r in retrieved) if retrieved else "No corpus excerpts."
    return facts, context[:8000]


def _apply_chapter_text(chapters: list[dict], chapter_num: int, title: str, text: str) -> list[dict]:
    entry = {
        "chapter_number": chapter_num,
        "title": title,
        "raw_text": text,
        "humanized_text": text,
        "edited_text": text,
        "verified_text": text,
        "word_count": len(text.split()),
    }
    out = list(chapters)
    idx = next((i for i, c in enumerate(out) if c.get("chapter_number") == chapter_num), None)
    if idx is not None:
        out[idx] = {**out[idx], **entry}
    else:
        out.append(entry)
    return out


def run_chapter_combined(state: dict[str, Any]) -> dict[str, Any]:
    """One LLM call: research context + write + polish + fact-check."""
    run_id = state.get("run_id", "")
    chapter_num = state.get("current_chapter", 1)
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    memory = state.get("memory", {})
    trace = get_trace_logger(run_id)

    ch = next((c for c in outline.get("chapters", []) if c["chapter_number"] == chapter_num), None)
    if not ch:
        return {}

    trace.log_agent_start("chapter_combined", {"chapter": chapter_num})
    start = time.perf_counter()

    facts, corpus = _rag_facts_for_chapter(run_id, brief, ch)
    research_by = dict(state.get("research_by_chapter", {}))
    research_by[chapter_num] = ChapterResearch(
        chapter_number=chapter_num,
        facts=facts,
        references=[f.get("source", "") for f in facts],
        glossary_candidates=[],
    ).model_dump()

    tone_fp = memory.get("tone_fingerprint") or {"tone": brief.get("tone", "Conversational"), "rules": []}
    if state.get("tone_override"):
        tone_fp = {"tone": state["tone_override"], "rules": []}

    target_words = ch.get("target_words", brief.get("words_per_chapter", 2500))
    prompt = load_prompt(
        "chapter_combined.txt",
        chapter_number=str(chapter_num),
        chapter_title=ch.get("title", ""),
        chapter_summary=ch.get("summary", ""),
        target_words=str(target_words),
        genre=brief.get("genre", "non-fiction"),
        tone_block=format_tone_block(tone_fp),
        memory_context=format_memory_context(memory, chapter_num),
        facts=f"{facts}\n\n{corpus}"[:10000],
    )
    text = invoke_text("chapter_combined", prompt, tier="strong", run_id=run_id)
    chapters = _apply_chapter_text(list(state.get("chapters", [])), chapter_num, ch.get("title", ""), text)

    trace.log_agent_end(
        "chapter_combined",
        {"chapter": chapter_num, "words": len(text.split())},
        (time.perf_counter() - start) * 1000,
    )
    return {"chapters": chapters, "research_by_chapter": research_by}


def run_chapters_batch(state: dict[str, Any]) -> dict[str, Any]:
    """One LLM call for all chapters when the job is small enough."""
    run_id = state.get("run_id", "")
    outline = state.get("outline", {})
    brief = state.get("brief", {})
    memory = state.get("memory", {})
    total = int(state.get("total_chapters") or len(outline.get("chapters", [])))
    trace = get_trace_logger(run_id)

    trace.log_agent_start("chapters_batch", {"chapters": total})
    start = time.perf_counter()

    specs_lines = []
    all_facts: list[dict[str, str]] = []
    corpus_parts: list[str] = []
    research_by = dict(state.get("research_by_chapter", {}))

    for ch in sorted(outline.get("chapters", []), key=lambda x: x["chapter_number"]):
        num = ch["chapter_number"]
        facts, corpus = _rag_facts_for_chapter(run_id, brief, ch)
        all_facts.extend(facts)
        corpus_parts.append(f"Chapter {num}:\n{corpus[:2000]}")
        research_by[num] = ChapterResearch(
            chapter_number=num,
            facts=facts,
            references=[f.get("source", "") for f in facts],
            glossary_candidates=[],
        ).model_dump()
        specs_lines.append(
            f"- Ch {num}: {ch.get('title', '')} — {ch.get('summary', '')} "
            f"(~{ch.get('target_words', brief.get('words_per_chapter', 2500))} words)"
        )

    tone_fp = memory.get("tone_fingerprint") or {"tone": brief.get("tone", "Conversational"), "rules": []}
    if state.get("tone_override"):
        tone_fp = {"tone": state["tone_override"], "rules": []}

    prompt = load_prompt(
        "chapters_batch.txt",
        title=outline.get("title", "Untitled"),
        topic=brief.get("topic", ""),
        genre=brief.get("genre", "non-fiction"),
        tone_block=format_tone_block(tone_fp),
        memory_context=format_memory_context(memory, 1),
        chapter_specs="\n".join(specs_lines),
        facts=str(all_facts)[:6000] + "\n\n" + "\n\n".join(corpus_parts)[:6000],
    )
    result = invoke_structured("chapters_batch", prompt, ChaptersBatchOutput, tier="strong", run_id=run_id)

    chapters = list(state.get("chapters", []))
    for item in result.chapters:
        title = item.title or next(
            (c.get("title", "") for c in outline.get("chapters", []) if c["chapter_number"] == item.chapter_number),
            f"Chapter {item.chapter_number}",
        )
        chapters = _apply_chapter_text(chapters, item.chapter_number, title, item.text)

    trace.log_agent_end("chapters_batch", {"chapters": len(result.chapters)}, (time.perf_counter() - start) * 1000)

    return {
        "chapters": chapters,
        "research_by_chapter": research_by,
        "current_chapter": total + 1,
    }


def run_chapter_split(state: dict[str, Any]) -> dict[str, Any]:
    """Original pipeline: separate LLM call per agent (large chapters only)."""
    s = dict(state)
    for fn in (run_researcher, run_writer, run_humanizer, run_editor, run_fact_checker):
        s = {**s, **fn(s)}
    return s


def run_chapter_pipeline(state: dict[str, Any]) -> dict[str, Any]:
    mode = state.get("chapter_pipeline_mode") or choose_chapter_pipeline_mode(state)

    if mode == "batch":
        if state.get("current_chapter", 1) != 1:
            return {}
        s = {**state, **run_memory_read(state)}
        s = {**s, **run_chapters_batch(s)}
        total = int(s.get("total_chapters") or len(s.get("outline", {}).get("chapters", [])))
        for num in range(1, total + 1):
            s = {**s, "current_chapter": num}
            s = {**s, **run_memory_write(s)}
        return {**s, "current_chapter": total + 1}

    s = {**state, **run_memory_read(state)}

    if mode == "combined":
        s = {**s, **run_chapter_combined(s)}
    else:
        s = {**s, **run_chapter_split(s)}

    return {**s, **run_memory_write(s)}
