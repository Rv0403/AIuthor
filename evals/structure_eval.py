"""Structural completeness evaluation."""
from typing import Any

REQUIRED_MANIFEST_KEYS = [
    "title",
    "half_title",
    "copyright_block",
    "dedication",
    "epigraph",
    "foreword",
    "preface",
    "acknowledgments",
    "introduction",
    "afterword",
    "appendix",
    "about_author",
    "back_cover_copy",
]


def eval_structure(manifest: dict[str, Any], outline: dict[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_MANIFEST_KEYS if not manifest.get(k)]
    chapters = manifest.get("chapters") or outline.get("chapters", [])
    score = max(0.0, 1.0 - (len(missing) / max(len(REQUIRED_MANIFEST_KEYS), 1)))
    return {
        "name": "structural_completeness",
        "score": round(score, 3),
        "max_score": 1.0,
        "missing_sections": missing,
        "chapter_count": len(chapters),
        "passed": len(missing) == 0 and len(chapters) > 0,
    }
