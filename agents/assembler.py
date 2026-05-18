"""Assembler Agent — front/back matter and export."""
from __future__ import annotations

import json
import time
from typing import Any

from agents.base import format_tone_block
from config import get_settings
from memory.memory_store import MemoryStore
from memory.schemas import BookManifest, BookMemory
from utils.file_generator import export_book
from utils.llm_client import invoke_structured, load_prompt
from utils.logger import get_trace_logger


def run_assembler(state: dict[str, Any]) -> dict[str, Any]:
    run_id = state.get("run_id", "")
    outline = state.get("outline", {})
    chapters = state.get("chapters", [])
    memory = state.get("memory", {})
    brief = state.get("brief", {})
    trace = get_trace_logger(run_id)
    settings = get_settings()

    trace.log_agent_start("assembler", {"chapters": len(chapters)})
    start = time.perf_counter()

    tone_fp = memory.get("tone_fingerprint") or {"tone": brief.get("tone", "Conversational")}
    glossary = {t["term"]: t["definition"] for t in memory.get("glossary_terms", []) if t.get("term")}

    prompt = load_prompt(
        "assembler.txt",
        title=outline.get("title", "Untitled"),
        tone_block=format_tone_block(tone_fp),
        topic=brief.get("topic", ""),
        reader=brief.get("reader", ""),
        chapter_titles="\n".join(f"{c['chapter_number']}. {c['title']}" for c in outline.get("chapters", [])),
        glossary_preview=str(list(glossary.items())[:20])[:3000],
    )
    manifest = invoke_structured("assembler", prompt, BookManifest, tier="strong", run_id=run_id)
    manifest_dict = manifest.model_dump()
    manifest_dict["chapters"] = sorted(chapters, key=lambda x: x.get("chapter_number", 0))
    manifest_dict["glossary"] = glossary or manifest_dict.get("glossary", {})

    paths = export_book(run_id, manifest_dict, outline)

    manifest_path = settings.outputs_dir / run_id / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")

    store = MemoryStore(run_id)
    store.save_snapshot(BookMemory.model_validate(memory), outline, chapters, brief)

    trace.log_agent_end("assembler", paths, (time.perf_counter() - start) * 1000)

    return {
        "manifest": manifest_dict,
        "output_paths": paths,
        "status": "completed",
    }
