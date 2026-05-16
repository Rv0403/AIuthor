"""Shared agent utilities."""
from __future__ import annotations

import json
from typing import Any

from memory.schemas import ToneFingerprint
from utils.llm_client import load_prompt


def format_tone_block(tone_fp: ToneFingerprint | dict[str, Any] | None) -> str:
    if tone_fp is None:
        return "Tone: Conversational (default)"
    if isinstance(tone_fp, ToneFingerprint):
        data = tone_fp.model_dump()
    else:
        data = tone_fp
    rules = "\n".join(f"- {r}" for r in data.get("rules", []))
    return f"Tone: {data.get('tone', 'Conversational')}\nRules:\n{rules}"


def format_memory_context(memory: dict[str, Any], chapter_num: int) -> str:
    parts = []
    callbacks = memory.get("callback_index", [])
    relevant = [c for c in callbacks if chapter_num in c.get("used_in", []) or c.get("introduced_in", 0) < chapter_num]
    if relevant:
        parts.append("Callbacks to weave in:\n" + json.dumps(relevant[:5], indent=2))
    facts = memory.get("fact_registry", [])
    if facts:
        parts.append("Established facts:\n" + json.dumps(facts[-10:], indent=2))
    chars = memory.get("character_bible", [])
    if chars:
        parts.append("Characters:\n" + json.dumps(chars, indent=2))
    return "\n\n".join(parts) if parts else "No prior memory context."
