"""Callback recall evaluation."""
from typing import Any


def eval_callbacks(chapters: list[dict[str, Any]], memory: dict[str, Any]) -> dict[str, Any]:
    callbacks = memory.get("callback_index", [])
    if not callbacks:
        return {"name": "callback_recall", "score": 1.0, "passed": True, "recall": 1.0}

    all_text = " ".join(
        ch.get("verified_text", ch.get("edited_text", "")) for ch in chapters
    ).lower()

    recalled = 0
    for cb in callbacks:
        snippet = (cb.get("callback_text") or "")[:30].lower()
        if snippet and snippet in all_text:
            recalled += 1

    recall = recalled / len(callbacks) if callbacks else 1.0
    return {
        "name": "callback_recall",
        "score": round(recall, 3),
        "recalled": recalled,
        "total": len(callbacks),
        "passed": recall >= 0.3,
    }
