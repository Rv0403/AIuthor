"""Regex heuristics for intent when LLM unavailable or to enrich mock."""
from __future__ import annotations

import re

from memory.schemas import IntentResult


def parse_intent_heuristic(user_input: str) -> IntentResult | None:
    text = user_input.lower()
    if "insert" in text and "chapter" in text:
        from agents.insert_clarification import parse_insert_after

        insert_after = parse_insert_after(user_input)
        run_m = re.search(r"run\s+([a-z0-9-]+)", text)
        return IntentResult(
            task_type="insert_chapter",
            topic="Personal Finance",
            insert_after=insert_after,
            source_run_id=run_m.group(1) if run_m else None,
        )
    if "regenerate" in text or "rewrite" in text:
        ch_m = re.search(r"chapter\s+(\d+)", text)
        tone = "Academic"
        for t in ("academic", "motivational", "witty", "conversational", "storyteller"):
            if t in text:
                tone = t.capitalize()
                if tone == "Storyteller":
                    pass
                break
        run_m = re.search(r"run\s+([a-z0-9-]+)", text)
        return IntentResult(
            task_type="tone_conversion",
            target_chapter=int(ch_m.group(1)) if ch_m else 3,
            tone=tone,
            source_run_id=run_m.group(1) if run_m else None,
        )
    if "novella" in text or "storyteller" in text:
        chars = []
        for name in ("Arjun", "Maya"):
            if name.lower() in text:
                chars.append(name)
        return IntentResult(
            task_type="generate_book",
            topic="Fiction",
            genre="fiction",
            tone="Storyteller",
            num_chapters=5,
            character_names=chars or ["Arjun", "Maya"],
            words_per_chapter=2000,
        )
    if "finance" in text or "personal finance" in text:
        ch_m = re.search(r"(\d+)[\s-]*chapter", text)
        return IntentResult(
            task_type="generate_book",
            topic="Personal Finance",
            reader="Beginners",
            tone="Conversational",
            genre="non-fiction",
            num_chapters=int(ch_m.group(1)) if ch_m else 10,
            words_per_chapter=2500 if "2500" in text else 500,
        )
    return None
