"""Run all evaluations and write report."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import get_settings
from evals.ai_tell_eval import eval_ai_tells
from evals.callback_eval import eval_callbacks
from evals.fact_coverage_eval import eval_fact_coverage
from evals.structure_eval import eval_structure
from evals.tone_eval import eval_tone_fidelity
from memory.memory_store import MemoryStore


def run_all_evals(run_id: str) -> dict[str, Any]:
    snap = MemoryStore.load_snapshot(run_id)
    if not snap:
        return {"error": f"No snapshot for run {run_id}"}

    manifest: dict[str, Any] = {}
    mp = get_settings().outputs_dir / run_id / "manifest.json"
    if mp.exists():
        manifest = json.loads(mp.read_text(encoding="utf-8"))
    chapters = snap.chapters or []
    memory = snap.memory.model_dump()
    outline = snap.outline or {}
    tone = (memory.get("tone_fingerprint") or {}).get("tone", snap.brief.get("tone", "Conversational") if snap.brief else "Conversational")

    all_text = "\n".join(ch.get("verified_text", "") for ch in chapters)
    research = {}

    results = [
        eval_structure(manifest or {"chapters": chapters}, outline),
        eval_ai_tells(all_text),
        eval_callbacks(chapters, memory),
        eval_tone_fidelity(all_text[:6000], tone, run_id),
    ]

    for ch in chapters[:3]:
        num = ch.get("chapter_number")
        results.append(
            eval_fact_coverage(
                ch.get("verified_text", ""),
                research,
            )
        )

    avg = sum(r["score"] for r in results) / len(results)
    report = {
        "run_id": run_id,
        "overall_score": round(avg, 3),
        "evaluations": results,
        "passed_all": all(r.get("passed", False) for r in results),
    }

    out = get_settings().outputs_dir / run_id / "eval_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def write_markdown_report(run_id: str, report: dict[str, Any]) -> Path:
    path = get_settings().project_root / "docs" / "evals_report.md"
    lines = [
        "# Evaluation Report",
        "",
        f"Run ID: `{run_id}`",
        f"Overall score: **{report.get('overall_score', 0)}**",
        "",
        "## Rubric Results",
        "",
    ]
    for ev in report.get("evaluations", []):
        status = "PASS" if ev.get("passed") else "FAIL"
        lines.append(f"- **{ev['name']}**: {ev['score']} ({status})")
    lines.extend(["", "## Failure Analysis", ""])
    for ev in report.get("evaluations", []):
        if not ev.get("passed"):
            lines.append(f"- {ev['name']}: {json.dumps({k: v for k, v in ev.items() if k not in ('name', 'score', 'passed')})}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
