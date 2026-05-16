"""AI-tell phrase detection."""
import re
from typing import Any

BANNED_PATTERNS = [
    r"\bdelve into\b",
    r"\blandscape of\b",
    r"in today'?s fast[- ]paced world",
    r"it'?s important to note",
    r"\bfurthermore\b",
    r"\bmoreover\b",
    r"not only .+ but also",
    r"\bleverage\b",
    r"\brobust solution\b",
    r"\bseamless\b",
]


def eval_ai_tells(text: str) -> dict[str, Any]:
    hits = []
    for pat in BANNED_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            hits.append({"pattern": pat, "match": m.group(0)})
    score = max(0.0, 1.0 - min(len(hits) * 0.15, 1.0))
    return {
        "name": "ai_tell_detection",
        "score": round(score, 3),
        "hits": hits[:20],
        "hit_count": len(hits),
        "passed": len(hits) == 0,
    }
