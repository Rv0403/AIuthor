"""Tonality fidelity — LLM judge + banned phrase check."""
from typing import Any

from utils.llm_client import invoke_text, load_prompt


def eval_tone_fidelity(text: str, tone: str, run_id: str = "") -> dict[str, Any]:
    sample = text[:4000]
    if not sample.strip():
        return {"name": "tone_fidelity", "score": 0.0, "passed": False}

    prompt = load_prompt(
        "eval_tone.txt",
        tone=tone,
        text_sample=sample,
    )
    try:
        raw = invoke_text("tone_eval", prompt, tier="cheap", run_id=run_id)
        import re

        m = re.search(r"(\d(?:\.\d)?)", raw)
        score = float(m.group(1)) / 5.0 if m else 0.7
    except Exception:
        score = 0.7

    return {
        "name": "tone_fidelity",
        "score": round(min(score, 1.0), 3),
        "tone": tone,
        "passed": score >= 0.6,
    }


def pick_best_opening(variants: list[str], tone: str, run_id: str = "") -> tuple[str, dict[str, Any]]:
    """Preference-lite: score openings and pick winner."""
    best = variants[0]
    best_score = -1.0
    best_eval = {}
    for v in variants:
        opening = v[:800]
        ev = eval_tone_fidelity(opening, tone, run_id)
        if ev["score"] > best_score:
            best_score = ev["score"]
            best = v
            best_eval = ev
    return best, best_eval
