"""Self-healing: TOC, callbacks, glossary after chapter insertion."""
from __future__ import annotations

import re
from typing import Any

from memory.schemas import BookMemory, CallbackRecord, DecisionLogEntry, FactRecord, GlossaryTerm


def renumber_chapters_after_insert(
    outline: dict[str, Any],
    chapters: list[dict[str, Any]],
    insert_after: int,
    new_chapter: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Insert new chapter after insert_after and renumber subsequent chapters."""
    ch_list = sorted(outline.get("chapters", []), key=lambda x: x["chapter_number"])
    new_num = insert_after + 1

    inserted_outline = {
        "chapter_number": new_num,
        "title": new_chapter.get("title", f"Chapter {new_num}"),
        "summary": new_chapter.get("summary", ""),
        "target_words": new_chapter.get("target_words", 2500),
    }

    updated_outline: list[dict[str, Any]] = []
    for ch in ch_list:
        n = ch["chapter_number"]
        if n <= insert_after:
            updated_outline.append(dict(ch))
        else:
            c = dict(ch)
            c["chapter_number"] = n + 1
            updated_outline.append(c)
    updated_outline.insert(insert_after, inserted_outline)

    sorted_content = sorted(chapters, key=lambda x: x.get("chapter_number", 0))
    updated_chapters: list[dict[str, Any]] = []
    for ch in sorted_content:
        n = ch.get("chapter_number", 0)
        if n <= insert_after:
            updated_chapters.append(dict(ch))
        else:
            c = dict(ch)
            c["chapter_number"] = n + 1
            updated_chapters.append(c)

    new_content = dict(new_chapter)
    new_content["chapter_number"] = new_num
    updated_chapters.insert(insert_after, new_content)

    outline["chapters"] = updated_outline
    return outline, updated_chapters


def repair_callbacks(memory: BookMemory, insert_after: int) -> BookMemory:
    repaired: list[CallbackRecord] = []
    for cb in memory.callback_index:
        data = cb.model_dump()
        if data["introduced_in"] > insert_after:
            data["introduced_in"] += 1
        data["used_in"] = [u + 1 if u > insert_after else u for u in data["used_in"]]
        repaired.append(CallbackRecord.model_validate(data))
    memory.callback_index = repaired
    return memory


def repair_glossary(memory: BookMemory, insert_after: int) -> BookMemory:
    repaired: list[GlossaryTerm] = []
    for term in memory.glossary_terms:
        data = term.model_dump()
        if data["introduced_in"] > insert_after:
            data["introduced_in"] += 1
        data["chapter_refs"] = [r + 1 if r > insert_after else r for r in data["chapter_refs"]]
        repaired.append(GlossaryTerm.model_validate(data))
    memory.glossary_terms = repaired
    return memory


def repair_fact_registry(memory: BookMemory, insert_after: int) -> BookMemory:
    repaired: list[FactRecord] = []
    for fact in memory.fact_registry:
        data = fact.model_dump()
        data["used_in"] = [u + 1 if u > insert_after else u for u in data["used_in"]]
        repaired.append(FactRecord.model_validate(data))
    memory.fact_registry = repaired
    return memory


def full_repair_after_insert(
    memory: BookMemory,
    outline: dict[str, Any],
    chapters: list[dict[str, Any]],
    insert_after: int,
    new_chapter: dict[str, Any],
) -> tuple[BookMemory, dict[str, Any], list[dict[str, Any]]]:
    outline, chapters = renumber_chapters_after_insert(outline, chapters, insert_after, new_chapter)
    memory = repair_callbacks(memory, insert_after)
    memory = repair_glossary(memory, insert_after)
    memory = repair_fact_registry(memory, insert_after)
    memory.decision_log.append(
        DecisionLogEntry(
            agent="repair",
            decision="chapter_insertion_repair",
            rationale=f"Renumbered and repaired memory after insert at {insert_after}",
            chapter_ref=insert_after + 1,
        )
    )
    return memory, outline, chapters


def update_toc_manifest(outline: dict[str, Any]) -> list[dict[str, str]]:
    entries = []
    for ch in outline.get("chapters", []):
        entries.append(
            {
                "number": str(ch["chapter_number"]),
                "title": ch["title"],
                "page": "",
            }
        )
    return entries


def patch_chapter_references_in_text(text: str, old_num: int, new_num: int) -> str:
    return re.sub(
        rf"\bChapter\s+{old_num}\b",
        f"Chapter {new_num}",
        text,
        flags=re.IGNORECASE,
    )
