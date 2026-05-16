"""Fact coverage — % research facts referenced in chapter."""
from typing import Any


def eval_fact_coverage(chapter_text: str, research: dict[str, Any]) -> dict[str, Any]:
    facts = research.get("facts", [])
    if not facts:
        return {"name": "fact_coverage", "score": 1.0, "passed": True, "coverage": 1.0}

    text_lower = chapter_text.lower()
    covered = 0
    for f in facts:
        fact_str = (f.get("fact") if isinstance(f, dict) else str(f)).lower()
        keywords = [w for w in fact_str.split() if len(w) > 5][:3]
        if any(kw in text_lower for kw in keywords):
            covered += 1

    coverage = covered / len(facts)
    return {
        "name": "fact_coverage",
        "score": round(coverage, 3),
        "covered": covered,
        "total": len(facts),
        "passed": coverage >= 0.2,
    }
